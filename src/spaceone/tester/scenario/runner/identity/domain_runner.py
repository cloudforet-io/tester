from spaceone.core.utils import random_string

# from spaceone.tester.scenario import Scenario
from spaceone.tester.scenario.runner.runner import ServiceRunner, print_json

__all__ = ['DomainRunner']


class DomainRunner(ServiceRunner):

    def __init__(self, clients, update_mode=False):
        # self.identity = client
        self.set_clients(clients)
        self.update_mode = update_mode

    def create_or_get_domain(self, domain_scenario):
        # We have to create or get domain
        # keyword: domain
        domain = None
        token = None
        domain_info = domain_scenario.get('domain', {})

        # print(f'self.update_mode {self.update_mode}')

        if self.update_mode:
            # If update_mode, find domain by name or domain_id.
            domain = self._find_domain(domain_info)
            token = domain_info.get('token')
            if domain and token is None:
                domainOwner = domain_scenario.get('domainOwner', {'owner_id': 'admin', 'password': 'admin1234567890'})
                token = self._get_domain_owner_token(domain, domainOwner['owner_id'], domainOwner['password'])

        if domain is None:
            domainOwner = domain_scenario.get('domainOwner', {'owner_id': 'admin', 'password': 'admin'})
            domain, token = self._create_domain(domain_scenario['domain'], domainOwner)

        if domain is None \
                or token is None:
            print(f'Unkown Error. Cannot prepare domain. (domain: {domain}, token: {token}')
            raise Exception(f'Unkown Error. Cannot prepare domain. (domain: {domain}, token: {token}')

        self.set_meta(token)

        self._list_provider(domain)

        return domain, token

    def _list_provider(self, domain):
        params = {'domain_id': domain.domain_id}
        print("######### List Provider ###########")
        providers = self.identity.Provider.list(params, metadata=self.get_meta())
        print_json(providers)

    def _find_domain(self, domain_info):
        param = {
            'query': {
                'filter': [
                    {'k': 'state', 'v': 'ENABLED', 'o': 'eq'}
                ]
            }
        }
        domain_id = domain_info.get('domain_id', None)
        domain_name = domain_info.get('name', None)

        if domain_id:
            param['domain_id'] = domain_id
        elif domain_name:
            param['name'] = domain_name
        else:
            print(f'############ CANNOT FIND DOMAIN (domain_name: {domain_name}, domain_id: {domain_id}) ############')
            return None

        print(f'############ FIND DOMAIN ({param}) ############')
        result = None
        result = self.identity.Domain.list(
            param
        )
        if len(result.results) == 1:
            domain = result.results[0]
            print_json(domain)
            print(f'############ FOUND - DOMAIN ({domain}) ############')
            return domain
        print(f'############ DOMAIN NOT FOUND ############')
        return None

    def _create_domain(self, param2={}, domainOwner={'owner_id':'admin', 'password':'admin1234567890'}):
        """ Create Domain
        1) Create Domain
        2) Create Domain Owner
        3) Create Token

        Args: json data
        param = {
            'name': 'root',
            'config': {
                'aaa': 'bbbb'
                },
            }
        }
        """
        param = {
            'name': random_string(),
            'tags': {'company': 'MEGAZONE CLOUD', 'Environment': 'EXP'},
            'config': {
                'icon': 'https://assets-console-spaceone-stg.s3.ap-northeast-2.amazonaws.com/mzc.jpg'
            }
        }
        param.update(param2)
        print("########## Create Domain ################")
        domain = self.identity.Domain.create(param)
        print_json(domain)
        self.append_terminator(self.identity.Domain.delete, {'domain_id': domain.domain_id})

        # This will cause auth failure
#        if param2.get('plugin_info'):
#            print("########## Update Domain Plugin ##########")
#            update_param = {
#                'domain_id': domain.domain_id,
#                'plugin_info': param2.get('plugin_info')
#            }
#            print(update_param)
#            domain = self.identity.Domain.update(update_param)
#            print_json(domain)
#

        print("########## Create Domain Owner ##########")
        owner_id = domainOwner['owner_id']
        owner_pw = domainOwner['password']

        param = {
            'owner_id': owner_id,
            'password': owner_pw,
            'name': 'Domain Admin',
            'timezone': 'Asia/Seoul',
            'email': 'admin' + random_string()[0:5] + '@spaceone.org',
            'domain_id': domain.domain_id
        }
        param.update(domainOwner)

        # Create Domain Owner
        owner = self.identity.DomainOwner.create(
            param
        )
        print("########## Create Domain Owner ###############")
        print_json(owner)
        self.append_terminator(
            self.identity.DomainOwner.delete,
            {'domain_id': domain.domain_id,
             'owner_id': owner.owner_id}
        )

        # Create Token
        token = self._get_domain_owner_token(domain, owner_id, owner_pw)

        return domain, token

    def _get_domain_owner_token(self, domain, owner_id='admin', owner_pw='admin'):
        token_param = {
            'user_id': owner_id,
            'user_type': 'DOMAIN_OWNER',
            'credentials': {
                'password': owner_pw
            },
            'domain_id': domain.domain_id
        }
        issue_token = self.identity.Token.issue(token_param)
        token = issue_token.access_token
        print("############## Domain Owner Token ################")
        print(token)
        print("")
        return token
