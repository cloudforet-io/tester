from spaceone.tester.scenario.runner.runner import ServiceRunner, print_json

__all__ = ['SecretRunner']


class SecretRunner(ServiceRunner):
    def __init__(self, clients, update_mode=False,
                 region_name2id={},
                 zone_name2id={},
                 pool_name2id={},
                 project_name2id={},
                 service_account_name2id={}
                 ):
        self.set_clients(clients)
        self.update_mode = update_mode
        self.region_name2id = region_name2id
        self.zone_name2id = zone_name2id
        self.pool_name2id = pool_name2id
        self.project_name2id = project_name2id
        self.service_account_name2id = service_account_name2id
        self.secret_name2id = {}

    def create_or_update_secrets(self, secrets, domain):
        for secret in secrets:
            if self.update_mode:
                secret_obj = self._find_secret(secret, domain)
                if secret_obj:
                    # secret is not mutable. It's only allow delete and create.
                    self._delete_secret(secret_obj)
            self._create_secret(secret, domain)
        return self.secret_name2id

    def _delete_secret(self, secret_obj):
        param = {
            'domain_id': secret_obj.domain_id,
            'secret_id': secret_obj.secret_id
        }
        self.secret.Secret.delete(param, metadata=self.get_meta())
        print("########### Secret DELETED ###############")

    def _find_secret(self, secret, domain):
        param = {
            'name': secret['name'],
            'domain_id': domain.domain_id
        }
        results = self.secret.Secret.list(param, metadata=self.get_meta())

        if len(results.results) >= 1:
            print(f'Found {len(results.results)} secret(s).')
            return results.results[0]
        return None

    def _create_secret(self, secret, domain):
        data = secret['data']

        default_param = secret
        # Project
        project_name = secret.get('project_name', None)
        if project_name:
            project_id = self.project_name2id[project_name]
            default_param['project_id'] = project_id
            del default_param['project_name']

        # ServiceAccount
        service_account_name = secret.get('service_account', None)
        if service_account_name:
            service_account_id = self.service_account_name2id[service_account_name]
            default_param['service_account_id'] = service_account_id
            del default_param['service_account']

        default_param.update({
            'domain_id': domain.domain_id
        })
        print(f"Create Secret: {default_param}")
        secret_obj = self.secret.Secret.create(default_param, metadata=self.get_meta())
        self.secret_name2id[secret_obj.name] = secret_obj.secret_id
        self.append_terminator(
            self.secret.Secret.delete,
            {
                'domain_id': domain.domain_id,
                'secret_id': secret_obj.secret_id
            }
        )
        print("########### Create SECRET ###############")
        print_json(secret_obj)
        issue = self.secret.Secret.get_data(
            {'secret_id': secret_obj.secret_id, 'domain_id': domain.domain_id},
            metadata=self.get_meta()
        )
        print("######### ISSUE SECRET #########")
        print_json(issue)
