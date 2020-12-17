from spaceone.tester.scenario.runner.runner import ServiceRunner, print_json

__all__ = ['ResourceGroupRunner']


class ResourceGroupRunner(ServiceRunner):

    def __init__(self, clients, update_mode=False,
                    project_name2id={}
                 ):
        self.set_clients(clients)
        self.update_mode = update_mode
        self.project_name2id = project_name2id
        self.resource_group_list = []
        self.resource_group_name2id = {}

    def create_or_update_resource_group(self, resource_groups, domain):
        for resource_group in resource_groups:
            resource_group_obj = None
            if self.update_mode:
                resource_group_obj = self._find_resource_group(collector, domain)
                if resource_group_obj:
                    resource_group_obj = self._update_resource_group(resource_group, resource_group_obj)

            if resource_group_obj is None:
                resource_group_obj = self._create_resource_group(collector, domain)
            self.resource_group_name2id[name] = resource_group_obj.resource_group_id 
        return self.resource_group_name2id

    def _update_resource_group(self, resource_group, resource_group_obj):
        params = resource_group
        resource_group_obj = self.inventory.ResourceGroup.update(params, metadata=self.get_meta())
        print("########### Update ResourceGroup ###############")
        print_json(resource_group_obj)
        self.resource_group_list.append(resource_group_obj)
        return resource_group_obj

    def _find_resource_group(self, resource_group, domain):
        name = resource_group['name']
        param = {
            'name': name,
            'domain_id': domain.domain_id
        }
        results = self.inventory.ResourceGroup.list(param, metadata=self.get_meta())
        if len(results.results) >= 1:
            print(f'Found {len(results.results)} "{name}" ResourceGroup')
            return results.results[0]
        return None

    def _create_resource_group(self, resource_group, domain):
        params = resource_group
       # project_id
        project_name = resource_group.get('project_name', None)
        if project_name:
            # Map to project_name to project_id
            project_id = self.project_name2id[project_name]
            params.update({'project_id': project_id})

        print(params)
        resource_group_obj = self.inventory.ResourceGroup.create(params, metadata=self.get_meta())
        print("########### Create ResourceGroup ###############")
        print_json(resource_group_obj)
        self.resource_group_list.append(resource_group_obj)
        self.append_terminator(
            self.inventory.ResourceGroup.delete,
            {
                'domain_id': domain.domain_id,
                'resource_group_id': resource_group_obj.resource_group_id
            }
        )
        return resource_group_obj
