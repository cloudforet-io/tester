# from spaceone.tester.scenario import Scenario

from spaceone.tester.scenario.runner.runner import ServiceRunner, print_json

__all__ = ['DataSourceRunner']


class DataSourceRunner(ServiceRunner):

    def __init__(self, clients, update_mode=False):
        self.set_clients(clients)
        self.update_mode = update_mode
        self.datasource_name2id = {}

    def register_or_update_datasources(self, datasources, domain):
        for datasource in datasources:
            if self.update_mode:
                datasource_obj = self._find_datasource(datasource, domain)
                if datasource_obj == None:
                    self._register_datasource(datasource, domain)
            else:
                self._register_datasource(datasource, domain)
        return self.datasource_name2id

    def _register_datasource(self, param, domain):
        param['domain_id'] = domain.domain_id

        ds_obj = self.monitoring.DataSource.register(param, metadata=self.get_meta())
        self.datasource_name2id[ds_obj.name] = ds_obj.data_source_id
        self.append_terminator(
            self.monitoring.DataSource.deregister,
            {
                'data_source_id': ds_obj.data_source_id,
                'domain_id': domain.domain_id
            }
        )
        print("########### Create DataSource #############")
        print_json(ds_obj)
        return ds_obj

    def _find_datasource(self, datasource, domain):
        param = {
            'name': datasource['name'],
            'domain_id': domain.domain_id
        }
        results = self.monitoring.DataSource.list(param, metadata=self.get_meta())

        if len(results.results) >= 1:
            print(f'Found {len(results.results)} datasource(s).')
            return results.results[0]
        return None

