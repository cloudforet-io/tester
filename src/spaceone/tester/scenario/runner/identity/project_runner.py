from spaceone.core.utils import random_string

from spaceone.tester.scenario.runner.runner import ServiceRunner, print_json

__all__ = ['ProjectRunner']


class ProjectRunner(ServiceRunner):

    def __init__(self, clients, update_mode=False):
        self.set_clients(clients)
        self.update_mode = update_mode
        self.project_name2pg_id = {}
        self.project_name2id = {}

    def create_or_update_project_groups(self, project_groups, domain):
        for group_name, project_list in project_groups.items():
            pg_id = None
            if self.update_mode:
                pg_id = self._find_project_group({'name': group_name}, domain)

            if pg_id is None:
                pg_id = self._create_project_group({'name': group_name}, domain)

            for project in project_list:
                self.project_name2pg_id[project] = pg_id

    def create_or_update_projects(self, projects, domain):
        for prj in projects:
            name = prj['name']
            prj.update({'project_group_id': self.project_name2pg_id[name]})

            project_id = None
            if self.update_mode:
                # find project
                project_id = self._find_and_update_project(prj, domain)

            if project_id is None:
                project_id = self._create_project(prj, domain)
            self.project_name2id[name] = project_id
        return self.project_name2id

    def map_members_into_projects(self, pm_param, domain):
        for project_name, user_infos in pm_param.items():
            project_id = self.project_name2id[project_name]
            print(f'project_name2id: {project_id}')
            for user_info in user_infos:
                param = {
                    'project_id': project_id,
                    'user_id': user_info['user_id'],
                    'labels': user_info.get('labels', [])
                }
                self._add_member_in_project(param, domain)

    def _add_member_in_project(self, param, domain):
        param.update({'domain_id': domain.domain_id})
        print(f'[_add_member_in_project] param: {param}')
        try:
            self.identity.Project.add_member(param, metadata=self.get_meta())
        except Exception as e:
            print(f'[_add_member_in_project] user already exist in project.')

    def _find_project_group(self, project_group, domain):
        pg_name = project_group.get('name')
        if pg_name is None:
            print('##### CANNOT FIND PROJECT GROUP #####')
            return None

        query = {
            'filter': [
                {'k': 'name', 'v': pg_name, 'o': 'eq'}
            ]
        }

        results = self.identity.ProjectGroup.list(
            {'query': query, 'domain_id': domain.domain_id},
            metadata=self.get_meta()
        )

        if len(results.results) == 1:
            # found
            pg = results.results[0]
            print('##### FOUDND PROJECT GROUP #####')
            print_json(pg)
            return pg.project_group_id

        if len(results.results) > 1:
            # Too many matched. Use one.
            print('##### FOUDND MULTIPLE PROJECT GROUP - Use the first one.#####')
            pg = results.results[0]
            print_json(pg)
            return pg.project_group_id
        else:
            print('##### PROJECT GROUP - NOT FOUDND #####')
            return None

    def _create_project_group(self, project_group, domain):
        pg_name = project_group.get('name', random_string()[0:10])
        param = {
            'name': pg_name,
            'domain_id': domain.domain_id
        }
        # Overwrite param, if needed
        param.update(project_group)

        pg = self.identity.ProjectGroup.create(
            param,
            metadata=self.get_meta()
        )
        print("########### Create Project-Group ###############")
        print_json(pg)
        self.append_terminator(self.identity.ProjectGroup.delete, {'project_group_id': pg.project_group_id,
                                                                   'domain_id': domain.domain_id})
        return pg.project_group_id

    def _find_and_update_project(self, project_param, domain):
        print("########### FIND Project ###############")
        query = {
            'filter': [
                {
                    'k': 'name',
                    'v': project_param['name'],
                    'o': 'eq'
                }
            ]
        }
        projects = self.identity.Project.list(
            {'query': query, 'domain_id': domain.domain_id},
            metadata=self.get_meta()
        )
        if len(projects.results) == 0:
            print("########### NOT FOUND - project ###############")
            return None
        if len(projects.results) > 1:
            print("########### Multiple projecs found - use one ###############")
        if len(projects.results) == 1:
            print("########### FOUND - project ###############")
        prj = projects.results[0]
        print_json(prj)

        project_param['project_id'] = prj.project_id
        project_param.update({'domain_id': domain.domain_id})
        prj = self.identity.Project.update(
            project_param,
            metadata=self.get_meta()
        )
        print("########### UDATE PROJECT ###############")

        return prj.project_id

    def _create_project(self, param2, domain):
        print("########### Create Project ###############")

        name = random_string()[0:10]
        param = {
            'name': name,
            'domain_id': domain.domain_id
        }
        # Overwrite param, if needed
        param.update(param2)

        project = self.identity.Project.create(
            param,
            metadata=self.get_meta()
        )
        print_json(project)
        self.append_terminator(
            self.identity.Project.delete,
            {'project_id': project.project_id, 'domain_id': domain.domain_id}
        )
        return project.project_id

