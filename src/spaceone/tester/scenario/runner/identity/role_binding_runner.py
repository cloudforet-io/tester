# from spaceone.tester.scenario import Scenario
import random

from spaceone.core.utils import random_string

from spaceone.tester.scenario.runner.runner import ServiceRunner, print_json

__all__ = ['RoleBindingRunner']


class RoleBindingRunner(ServiceRunner):

    def __init__(self, clients, update_mode=False, role_name2id={}):
        self.set_clients(clients)
        self.update_mode = update_mode
        self.role_binding_name2id = {}
        self.role_name2id = role_name2id

    def create_or_update_role_bindings(self, scenario_role_bindings, domain):
        if domain is None:
            raise Exception(f'Cannot create role binding. (domain={domain}')

        for (resource_id, role_name) in scenario_role_bindings.items():
            print(f"{resource_id} as {role_name}")
            if role_name in self.role_name2id:
                role_binding_data = _prepare_role_binding_data(resource_id, self.role_name2id[role_name])

                role = None
                if self.update_mode:
                    print("Not support Role Binding update")
                    continue

                if role is None:
                    role_binding_id = self._create_role_binding(role_binding_data, domain.domain_id)

    def _create_role_binding(self, role_binding_data, domain_id):
        print("########### Create Role Binding ###############")
        role_binding_data.update({'domain_id': domain_id})
        #print(f"meta: {self.get_meta()}")
        print(f"role_binding_data: {role_binding_data}")
        role = self.identity.RoleBinding.create(
            role_binding_data,
            metadata=self.get_meta()
        )
        self.append_terminator(self.identity.RoleBinding.delete,
                               {'domain_id': domain_id,
                                'role_binding_id': role.role_binding_id})
        print_json(role)
        return role.role_binding_id

def _prepare_role_binding_data(resource_id, role_id):
    default_role = {
        'resource_type': 'identity.User',
        'resource_id': resource_id,
        'role_id': role_id
    }
    # Overwrite param, if needed
    return default_role
