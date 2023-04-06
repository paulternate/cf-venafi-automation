#!/bin/bash

# example usage from CloudFormation UserData:
# UserData:
#   Fn::Base64: !Sub |
#     #!/bin/bash
#
#     export APP_NAME=${AppName}
#     export CONTAINER_IMAGE=${ContainerImage}
#     export CONTAINER_PORT=${ContainerPort}
#     export TLSPK_SA_USER_ID=${TLSPKSAUserID}
#     export TLSPK_SA_USER_SECRET='${TLSPKSAUserSecret}''
#     export TLSPC_API_KEY=${TLSPCAPIKey}
#
#     curl --silent https://hackathon2023-public.s3.amazonaws.com/2023-04/tls-app-deployer.sh | bash

set -e # any non-zero return/exit codes cause an immediate abort

function logger(){
  echo "tls-app-deployer.sh: $1"
}

function check_arch() {
  logger "checking arch"
  if [[ "$(uname -m)" != "x86_64" ]]; then
    logger "architecture $(uname -m) not supported"
    return 1
  fi
}

# TODO this code ain't great
os=unknown
os_user=unknown
function check_os() {
  logger "checking os"
  distro=$(awk -F= '/^NAME/{print $2}' /etc/os-release | tr -d '"')

  case $distro in
    "Amazon Linux") # |"Red Hat Enterprise Linux") <- WIP https://docs.docker.com/engine/install/rhel/ 
      os=amzn
      os_user=ec2-user
      return 0
      ;;
    "Ubuntu")
      os=ubuntu
      os_user=ubuntu
      return 0
      ;;
    *)
      logger "${distro} not supported"
      return 1
      ;;
  esac
}

function check_vars() {
  logger "checking vars"
  local result=0
  vars=("APP_NAME" "CONTAINER_IMAGE" "CONTAINER_PORT" "TLSPK_SA_USER_ID" "TLSPK_SA_USER_SECRET" "TLSPC_API_KEY")
  for var in "${vars[@]}"; do
    if [[ -z "${!var}" ]]; then
      logger "$var is not set"
      result=1
    fi
  done
  return ${result}
}

function switch_user() {
  logger "switching to ${os_user}"
  su ${os_user}
}

# [main]
logger "START"

if ! check_arch || ! check_os || ! check_vars; then
  logger "ABORT"
  exit 1
fi

switch_user
install_software_${os}
# start_docker
# create_cluster
# derive_org_from_user
# deploy_tlspk_agent
# install_operator
# deploy_operator_components
# deploy_self_signed_issuer
# create_demo_certs

logger "DONE"
exit 0

# ----------------------------------------- EVERYTHING BELOW IGNORED --------------------------------------

logger "START"

app_name=$1                 # e.g. test-container
container_image=$2          # e.g. amcginlay/test-container:1.0.0
container_port=$3           # e.g. 80
tlspk_org=$4                # e.g. gallant-wright
tlspc_api_key=$5            # from https://ui.venafi.cloud/platform-settings/user-preferences?key=api-keys
tlspc_zone=$(cat zone.txt)  # e.g. BUILTIN/Built-In CA Template
tlspk_json_token_content=$(cat token.json)
k8s_name=${app_name}
k8s_name_tlspk=$(tr "-" "_" <<< ${k8s_name})

echo "${script}: pwd=$(pwd)"
echo "${script}: app_name=${app_name}"
echo "${script}: container_image=${container_image}"
echo "${script}: container_port=${container_port}"
echo "${script}: tlspk_org=${tlspk_org}"
echo "${script}: tlspc_api_key=${tlspc_api_key}"
echo "${script}: tlspc_zone=${tlspc_zone}"
echo "${script}: tlspk_json_token_content=${tlspk_json_token_content}"
echo "${script}: k8s_name=${k8s_name}"
echo "${script}: k8s_name_tlspk=${k8s_name_tlspk}"

echo "${script}: installing docker"
yum update -y
yum install -y docker jq
systemctl enable docker.service
systemctl start docker.service

echo "${script}: installing kubectl"
curl -O -s https://s3.us-west-2.amazonaws.com/amazon-eks/1.25.6/2023-01-30/bin/linux/amd64/kubectl
chmod +x ./kubectl
mv ./kubectl /usr/local/bin/

echo "${script}: installing k3d + creating cluster"
curl -s https://raw.githubusercontent.com/k3d-io/k3d/main/install.sh | bash
k3d cluster create ${k8s_name} -p "80:80@loadbalancer" -p "443:443@loadbalancer" --wait
k3d kubeconfig merge ${k8s_name} --kubeconfig-merge-default --kubeconfig-switch-context

echo "${script}: installing jsctl for TLSPK"
wget https://github.com/jetstack/jsctl/releases/download/v0.1.17/jsctl-linux-amd64.tar.gz
tar -zxvf jsctl-linux-amd64.tar.gz
mv ./jsctl-linux-amd64/jsctl /usr/local/bin/

echo "${script}: hacking the TLSPK creds"
### jsctl auth login --credentials ${creds_file}
### jsctl config set organization gallant-wright
export HOME=/
mkdir ${HOME}.jsctl
echo $tlspk_json_token_content > ${HOME}.jsctl/token.json
echo '{ "organization": "'"${tlspk_org}"'" }' > ${HOME}.jsctl/config.json
chmod 600 ${HOME}.jsctl/token.json ${HOME}.jsctl/config.json

echo "${script}: connecting to TLSPK and deploying operator components (e.g. cert-manager)"
jsctl clusters connect ${k8s_name_tlspk}
sleep 10 && jsctl operator deploy --auto-registry-credentials
sleep 2 && kubectl -n jetstack-secure wait --for=condition=Available=True --all deployments --timeout=-1s
sleep 5 && jsctl operator installations apply --auto-registry-credentials --cert-manager-replicas 1
sleep 2 && kubectl -n jetstack-secure wait --for=condition=Available=True --all deployments --timeout=-1s

echo "${script}: installing the TLSPC issuer"
kubectl -n jetstack-secure create secret generic venafi-token --from-literal=token=${tlspc_api_key}
kubectl patch installation jetstack-secure --type merge --patch-file <(cat <<EOF
spec:
  issuers:
    - clusterScope: true
      name: venafi
      venafi:
        zone: ${tlspc_zone}
        cloud:
          apiTokenSecretRef:
            name: venafi-token
            key: token
EOF
)

echo "${script}: deploying app and adding ingress rule"
kubectl create deployment ${app_name} --image ${container_image} --port ${container_port}
kubectl expose deployment ${app_name} --port 8080 --target-port ${container_port}

cat << EOF | kubectl apply -f -
# apiVersion: networking.k8s.io/v1beta1 # for k3s < v1.19
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: ${app_name}
  annotations:
    cert-manager.io/cluster-issuer: "venafi"
    cert-manager.io/common-name: "${app_name}.com"
    ingress.kubernetes.io/ssl-redirect: "true"
spec:
  tls:
  - hosts:
    - ${app_name}.com
    secretName: ${app_name}-com-tls
  rules:
  - host: ${app_name}.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: ${app_name}
            port:
              number: 8080
EOF

echo "${script}: END"

# you can now navigate to http://<PUBLIC_IP> to reach test-container