function lambda_handler() {
    EVENT_DATA=$1

    RESPONSE="{\"statusCode\": 200, \"body\": \"Hello from Lambda!\"}"
    echo $RESPONSE

    # no further progress here until/unless we can port the cfnrespone module to bash:
    # https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/cfn-lambda-function-code-cfnresponsemodule.html
}
