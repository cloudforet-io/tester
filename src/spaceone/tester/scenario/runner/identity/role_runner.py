# from spaceone.tester.scenario import Scenario
import random

from spaceone.core.utils import random_string

from spaceone.tester.scenario.runner.runner import ServiceRunner, print_json

__all__ = ['RoleRunner']


class RoleRunner(ServiceRunner):

    def __init__(self, clients, update_mode=False):
        self.set_clients(clients)
        self.update_mode = update_mode
        self.role_name2id = {}

    def create_or_update_role(self, scenario_roles, domain):
        if domain is None:
            raise Exception(f'Cannot create roles. (domain={domain}')

        for scenario_role in scenario_roles:
            if isinstance(scenario_role, dict):
                role_data = _prepare_role_data(scenario_role)

                role = None
                if self.update_mode:
                    role = self._get_role(role_data, domain.domain_id)
                    if role:
                        role = self._update_role(role_data, domain.domain_id)

                if role is None:
                    role_id = self._create_role(role_data, domain.domain_id)
                    self.role_name2id[role_data['name']] = role_id

        return self.role_name2id

    def _get_role(self, role_data, domain_id):
        if 'role_id' not in role_data:
            return None
        role = None
        print("########### GET Role ###############")
        try:
            role = self.identity.Role.get(
                {'role_id': role_data['role_id'], 'domain_id': domain_id},
                metadata=self.get_meta()
            )
        except:
            print("########### NOT FOUND - role ###############")

        if role:
            print("########### Role FOUND ###############")
            return role
        return None

    def _create_role(self, role_data, domain_id):
        print("########### Create Role ###############")
        role_data.update({'domain_id': domain_id})
        #print(f"meta: {self.get_meta()}")
        print(f"role_data: {role_data}")
        role = self.identity.Role.create(
            role_data,
            metadata=self.get_meta()
        )
        self.append_terminator(self.identity.Role.delete,
                               {'domain_id': domain_id,
                                'role_id': role.role_id})
        print_json(role)
        return role.role_id

    def _update_role(self, role_data, domain_id):
        role = None
        try:
            # update_role
            role_data.update({'domain_id': domain_id})

            role = self.identity.Role.update(
                role_data,
                metadata=self.get_meta()
            )
            print("########### Update Role - update-mode ###############")
            print_json(role)
        except Exception as e:
            print(f'Cannot update role. (role={role}')
        return role

def _prepare_role_data(scenario_role):
    default_role = {}
    # Overwrite param, if needed
    default_role.update(scenario_role)
    return default_role
