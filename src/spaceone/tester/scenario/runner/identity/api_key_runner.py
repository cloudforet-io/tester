from spaceone.tester.scenario.runner.runner import ServiceRunner, print_json, to_json

__all__ = ['APIKeyRunner']


class APIKeyRunner(ServiceRunner):

    def __init__(self, clients, update_mode=False):
        self.set_clients(clients)
        self.update_mode = update_mode

    def create_user_api_keys(self, api_key_users, domain):
        result = {}
        for api_key_user in api_key_users:
            api_default_param = {
                'user_id': api_key_user['user_id'],
                'domain_id': domain.domain_id
            }
            api_key_obj = self.identity.APIKey.create(
                api_default_param,
                metadata=self.get_meta()
            )
            result[api_key_user['user_id']] = api_key_obj.api_key
            print("########### Create a new user API KEY ###############")
            print_json(api_key_obj)
            self.append_terminator(
                self.identity.APIKey.delete,
                {'domain_id': domain.domain_id, 'api_key_id': api_key_obj.api_key_id}
            )
        return result
