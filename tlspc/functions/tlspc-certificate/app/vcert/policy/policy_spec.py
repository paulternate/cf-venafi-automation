#
# Copyright 2021 Venafi, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#  http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

DEFAULT_CA = "BUILTIN\\Built-In CA\\Default Product"


class PolicySpecification:
    def __init__(self, owners=None, users=None, user_access=None, approvers=None, policy=None, defaults=None):
        """
        :param list[str] owners:
        :param list[str] users:
        :param str user_access:
        :param list[str] approvers:
        :param Policy policy:
        :param Defaults defaults:
        """
        self.owners = owners if owners else []
        self.users = users if users else []
        self.user_access = user_access
        self.approvers = approvers if approvers else []
        self.policy = policy
        self.defaults = defaults


class Policy:
    def __init__(self, domains=None, wildcard_allowed=None, max_valid_days=None, cert_auth=None, subject=None,
                 key_pair=None, subject_alt_names=None, auto_installed=None):
        """
        :param list[str] domains:
        :param bool wildcard_allowed:
        :param int max_valid_days:
        :param str cert_auth:
        :param Subject subject:
        :param KeyPair key_pair:
        :param SubjectAltNames subject_alt_names:
        :param bool auto_installed:
        """
        self.domains = domains if domains else []
        self.wildcard_allowed = wildcard_allowed
        self.max_valid_days = max_valid_days
        self.certificate_authority = cert_auth if cert_auth else DEFAULT_CA
        self.subject = subject
        self.key_pair = key_pair
        self.subject_alt_names = subject_alt_names
        self.auto_installed = auto_installed


class Subject:
    def __init__(self, orgs=None, org_units=None, localities=None, states=None, countries=None):
        """
        :param list[str] orgs:
        :param list[str] org_units:
        :param list[str] localities:
        :param list[str] states:
        :param list[str] countries:
        """
        self.orgs = orgs if orgs else []
        self.org_units = org_units if org_units else []
        self.localities = localities if localities else []
        self.states = states if states else []
        self.countries = countries if countries else []


class KeyPair:
    def __init__(self, key_types=None, rsa_key_sizes=None, elliptic_curves=None, service_generated=None,
                 reuse_allowed=None):
        """
        :param list[str] key_types:
        :param list[int] rsa_key_sizes:
        :param list[str] elliptic_curves:
        :param bool service_generated:
        :param bool reuse_allowed:
        """
        self.key_types = key_types if key_types else []
        self.rsa_key_sizes = rsa_key_sizes if rsa_key_sizes else []
        self.elliptic_curves = elliptic_curves if elliptic_curves else []
        self.service_generated = service_generated
        self.reuse_allowed = reuse_allowed


class SubjectAltNames:
    def __init__(self, dns_allowed=None, email_allowed=None, ip_allowed=None, upn_allowed=None, uri_allowed=None,
                 uri_protocols=None, ip_constraints=None):
        """
        :param bool dns_allowed:
        :param bool email_allowed:
        :param bool ip_allowed:
        :param bool upn_allowed:
        :param bool uri_allowed:
        :param list[str] uri_protocols:
        :param list[str] ip_constraints:
        """
        self.dns_allowed = dns_allowed
        self.email_allowed = email_allowed
        self.ip_allowed = ip_allowed
        self.upn_allowed = upn_allowed
        self.uri_allowed = uri_allowed
        self.uri_protocols = uri_protocols
        self.ip_constraints = ip_constraints


class Defaults:
    def __init__(self, d_domain=None, d_subject=None, d_key_pair=None, auto_installed=None):
        """
        :param str d_domain:
        :param DefaultSubject d_subject:
        :param DefaultKeyPair d_key_pair:
        :param bool auto_installed:
        """
        self.domain = d_domain
        self.subject = d_subject
        self.key_pair = d_key_pair
        self.auto_installed = auto_installed


class DefaultSubject:
    def __init__(self, org=None, org_units=None, locality=None, state=None, country=None):
        """
        :param str org:
        :param list[str] org_units:
        :param str locality:
        :param str state:
        :param str country:
        """
        self.org = org
        self.org_units = org_units if org_units else []
        self.locality = locality
        self.state = state
        self.country = country


class DefaultKeyPair:
    def __init__(self, key_type=None, rsa_key_size=None, elliptic_curve=None, service_generated=None):
        """
        :param str key_type:
        :param int rsa_key_size:
        :param str elliptic_curve:
        :param bool service_generated:
        """
        self.key_type = key_type
        self.rsa_key_size = rsa_key_size
        self.elliptic_curve = elliptic_curve
        self.service_generated = service_generated
