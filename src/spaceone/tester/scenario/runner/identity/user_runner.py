# from spaceone.tester.scenario import Scenario
import random

from spaceone.core.utils import random_string

from spaceone.tester.scenario.runner.runner import ServiceRunner, print_json

__all__ = ['UserRunner']


class UserRunner(ServiceRunner):

    def __init__(self, clients, update_mode=False):
        self.set_clients(clients)
        self.update_mode = update_mode

    def create_or_update_user(self, scenario_users, domain):
        if domain is None:
            raise Exception(f'Cannot create users. (domain={domain}')

        for scenario_user in scenario_users:
            if isinstance(scenario_user, dict):
                user_data = _prepare_user_data(scenario_user)

                user = None
                if self.update_mode:
                    user = self._get_user(user_data, domain.domain_id)
                    if user:
                        user = self._update_user(user_data, domain.domain_id)

                if user is None:
                    user = self._create_user(user_data, domain.domain_id)

    def _get_user(self, user_data, domain_id):
        # query = {'filter': [
        #     {'k': 'user_id',
        #      'v': user_data['name'],
        #      'o': 'eq'}]
        # }
        print("########### GET USER ###############")
        user = None
        try:
            user = self.identity.User.get(
                {'user_id': user_data['user_id'], 'domain_id': domain_id},
                metadata=self.get_meta()
            )
        except:
            print("########### NOT FOUND - user ###############")

        if user:
            print("########### USER FOUND ###############")
            return user
        return None

    def _create_user(self, user_data, domain_id):
        print("########### Create User ###############")
        user_data.update({'domain_id': domain_id})
        #print(f"meta: {self.get_meta()}")
        print(f"user_data: {user_data}")
        user = self.identity.User.create(
            user_data,
            metadata=self.get_meta()
        )
        self.append_terminator(self.identity.User.delete,
                               {'domain_id': domain_id,
                                'user_id': user.user_id})
        print_json(user)
        return user

    def _update_user(self, user_data, domain_id):
        user = None
        try:
            # update_user
            user_data.update({'domain_id': domain_id})

            user = self.identity.User.update(
                user_data,
                metadata=self.get_meta()
            )
            print("########### Update User - update-mode ###############")
            print_json(user)
        except Exception as e:
            print(f'Cannot update user. (user={user}')
        return user

def _prepare_user_data(scenario_user):
    lang_code = random.choice(['ko', 'en'])
    user_id = random_string()[0:10]

    default_user = {
        'user_id': user_id,
        'password': user_id,
        'name': 'Steven' + random_string()[0:5],
        'language': lang_code,
        'timezone': 'Asia/Seoul', 'tags': {'company':'spaceone', 'role': 'developer'},
        'email': 'stark' + random_string()[0:5] + '@spaceone.org'
    }
    # Overwrite param, if needed
    default_user.update(scenario_user)
    return default_user
