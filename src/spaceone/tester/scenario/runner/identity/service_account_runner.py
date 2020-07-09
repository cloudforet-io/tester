from spaceone.core.utils import random_string

from spaceone.tester.scenario.runner.runner import ServiceRunner, print_json

__all__ = ['ServiceAccountRunner']


class ServiceAccountRunner(ServiceRunner):

    def __init__(self, clients, update_mode=False, project_name2id={}):
        self.set_clients(clients)
        self.update_mode = update_mode
        self.project_name2id = project_name2id
        self.service_account_name2id = {}

    def create_or_update_service_accounts(self, service_accounts, domain):
        for service_account in service_accounts:
            name = service_account['name']
            service_account_id = None
            if self.update_mode:
                # find service account
                service_account_id = self._find_and_update_service_account(service_account, domain)

            if service_account_id is None:
                service_account_id = self._create_service_account(service_account, domain)
            self.service_account_name2id[name] = service_account_id
        return self.service_account_name2id

    def _find_and_update_service_account(self, service_account_param, domain):
        print("########### FIND ServiceAccount ###############")
        query = {
            'filter': [
                {
                    'k': 'name',
                    'v': service_account_param['name'],
                    'o': 'eq'
                }
            ]
        }
        service_accounts = self.identity.ServiceAccount.list(
            {'query': query, 'domain_id': domain.domain_id},
            metadata=self.get_meta()
        )
        if len(service_accounts.results) == 0:
            print("########### NOT FOUND - service accounts ###############")
            return None
        if len(service_accounts.results) > 1:
            print("########### Multiple service accounts found - use one ###############")
        if len(service_accounts.results) == 1:
            print("########### FOUND - ServiceAccount ###############")
        service_account = service_accounts.results[0]
        print_json(service_account)

        service_account_param['service_account_id'] = service_account.service_account_id
        service_account_param.update({'domain_id': domain.domain_id})
        # provider can not be updated
        if 'provider' in service_account_param:
            del service_account_param['provider']
        service_account = self.identity.ServiceAccount.update(
            service_account_param,
            metadata=self.get_meta()
        )
        print("########### UDATE ServiceAccount ###############")

        return service_account.service_account_id

    def _create_service_account(self, param2, domain):
        print("########### Create Service Account ###############")

        name = random_string()[0:10]
        param = {
            'name': name,
            'domain_id': domain.domain_id
        }
        # Overwrite param, if needed
        param.update(param2)

        # project_id
        project_name = param.get('project_name', None)
        if project_name:
            project_id = self.project_name2id[project_name]
            param['project_id'] = project_id
            del param['project_name']

        service_account = self.identity.ServiceAccount.create(
            param,
            metadata=self.get_meta()
        )
        print_json(service_account)
        self.append_terminator(
            self.identity.ServiceAccount.delete,
            {'service_account_id': service_account.service_account_id, 'domain_id': domain.domain_id}
        )
        return service_account.service_account_id

