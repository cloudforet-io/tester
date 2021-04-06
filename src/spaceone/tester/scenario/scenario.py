import json
import logging
import os

import consul
from spaceone.core.utils import deep_merge

from spaceone.tester.scenario.runner.identity.api_key_runner import APIKeyRunner
from spaceone.tester.scenario.runner.identity.domain_runner import DomainRunner
from spaceone.tester.scenario.runner.identity.project_runner import ProjectRunner
from spaceone.tester.scenario.runner.identity.role_runner import RoleRunner
from spaceone.tester.scenario.runner.identity.role_binding_runner import RoleBindingRunner
from spaceone.tester.scenario.runner.identity.user_runner import UserRunner
from spaceone.tester.scenario.runner.identity.service_account_runner import ServiceAccountRunner
from spaceone.tester.scenario.runner.inventory.resource_group_runner import ResourceGroupRunner
from spaceone.tester.scenario.runner.inventory.collector_runner import CollectorRunner
from spaceone.tester.scenario.runner.inventory.region_zone_pool_runner import RegionZonePoolRunner
from spaceone.tester.scenario.runner.repository.repository_runner import RepositoryRunner
from spaceone.tester.scenario.runner.runner import ServiceRunner
from spaceone.tester.scenario.runner.secret.secret_runner import SecretRunner
from spaceone.tester.scenario.runner.secret.secret_group_runner import SecretGroupRunner
from spaceone.tester.scenario.runner.monitoring.datasource_runner import DataSourceRunner
from spaceone.tester.scenario.runner.statistics.schedule_runner import ScheduleRunner
from spaceone.tester.scenario.runner.power_scheduler.schedule_runner import ScheduleRunner as PowerScheduleRunner

__ALL__ = ['Scenario']

_LOGGER = logging.getLogger(__name__)

meta = []
terminate_list = []


class Scenario(object):
    update_mode = False
    scenario = {}
    clients = {}
    is_terminate = False
    is_update_mode = False
    is_update_supervisor_token = False
    params = {}
    consul = None

    def __init__(self, scenario_uri, clients, scenario_params):
        self.parse_params(scenario_params)
        self.load_scenario(scenario_uri)
        self.clients = clients
        # self.set_client(clients)

    def parse_params(self, parse_params):
        def _put(d, keys, item):
            if "." in keys:
                key, rest = keys.split(".", 1)
                if key not in d:
                    d[key] = {}
                _put(d[key], rest, item)
            else:
                d[keys] = item

        if isinstance(parse_params, str):
            for param in parse_params.split(','):
                items = param.split('=')
                if len(items) != 2:
                    continue
                if items[1].lower() == 'true':
                    items[1] = True
                elif items[1].lower() == 'false':
                    items[1] = False
                _put(self.params, items[0], items[1])

    def load_scenario(self, scenario_uri):
        # load scenario
        try:
            with open(scenario_uri, 'r', encoding='utf-8') as f:
                self.scenario = json.load(f)
                _LOGGER.debug(f'[load_scenario] scenario is loaded. (scenario_uri={scenario_uri})')
                # self._run_scenario()
        except Exception as e:
            print(scenario_uri)
            _LOGGER.warning(f'[setUpClass] SKIP handling Scenario file. (e={e}')
            return

        _LOGGER.debug(f'custom param: {self.params}')
        self.scenario = deep_merge(self.params, self.scenario)

        options = self.scenario.get('options', {})
        self.update_mode = options.get('update_mode', False)
        options = self.scenario.get('options', {})
        self.is_terminate = options.get('terminate', False)
        self.is_update_mode = options.get('update_mode', False)
        self.is_update_supervisor_token = options.get('update_supervisor_token', False)

    def terminate(self):
        ServiceRunner.terminate()

    def delete(self):
        SecretRunner.delete()

    def set_meta(self, token):
        meta.append(('token', token))

    def get_meta(self):
        return meta

    def run_scenario(self):
        # Create Domain
        _LOGGER.debug(f'[_run_scenario] .....')

        domain_scenario = self.scenario.get('domain', None)
        consul = self.scenario.get('consul', None)
        self.consul = consul

        domain = None   # For empty scenario
        if domain_scenario:

            # Create or Update - Domain
            domain_tester = DomainRunner(self.clients, update_mode=self.is_update_mode)
            domain, token = domain_tester.create_or_get_domain(domain_scenario)

            # Add token to config server
            #if self.is_update_supervisor_token:
            #    self._update_supervisor_token(consul, token)
            if token:
                self.set_meta(token)

            # Role
            scenario_roles = domain_scenario.get('roles', [])
            role_runner = RoleRunner(self.clients, update_mode=self.is_update_mode)
            role_name2id = role_runner.create_or_update_role(scenario_roles, domain)

            # Create or Update - Users
            scenario_users = domain_scenario.get('users', [])
            user_runner = UserRunner(self.clients, update_mode=self.is_update_mode)
            user_runner.create_or_update_user(scenario_users, domain)

            # Create - User API Key
            api_key_users = domain_scenario.get("api_key_users", [])
            api_key_runner = APIKeyRunner(self.clients, update_mode=self.is_update_mode)
            api_keys = api_key_runner.create_user_api_keys(api_key_users, domain)
            # Add token to config server
            if self.is_update_supervisor_token:
                #self._update_supervisor_token(consul, api_key['supervisor'])
                for k, token in api_keys.items():
                    self._update_token(consul, k, token)
                # Update domain_id
                self._update_domain_at_consul(consul, 'domain_id', domain.domain_id)

            # ### Projects ###
            print("Projects")
            # Create or Update - Project Group
            project_groups = domain_scenario.get('project_group', {})
            project_runner = ProjectRunner(self.clients, update_mode=self.is_update_mode)
            project_runner.create_or_update_project_groups(project_groups, domain)

            # Create or Update - Project
            projects_param = domain_scenario.get('projects', [])
            project_name2id = project_runner.create_or_update_projects(projects_param, domain)

            # Project member mapping
            pm_param = domain_scenario.get('project_member', {})
            project_runner.map_members_into_projects(pm_param, domain)

            # Role Binding mapping
            print("Role Binding")
            scenario_role_binding_user = domain_scenario.get('role_binding_user', {})
            role_binding_user_runner = RoleBindingRunner(self.clients,
                                                update_mode=self.is_update_mode,
                                                role_name2id=role_name2id)
            role_name2id = role_binding_user_runner.create_or_update_role_bindings(scenario_role_binding_user, domain)


            # ### Repository ###
            # Local Repository
            repository_runner = RepositoryRunner(self.clients, update_mode=self.is_update_mode)
            local_repo = domain_scenario.get("local_repository", None)
            if local_repo:
                local_repo['domain_id'] = domain.domain_id
                repository_runner.register_local_repository(local_repo)
            else:
                print("Skip Register local repo")

            # Remote Repository
            remote_repos = domain_scenario.get("remote_repositories", [])
            if len(remote_repos) > 0:
                repository_runner.register_remote_repositories(remote_repos, domain)
            else:
                print("Skip Register remote repo")

            # Service Account
            service_accounts = domain_scenario.get('service_accounts', {})
            service_account_runner = ServiceAccountRunner(
                self.clients,
                update_mode=self.is_update_mode,
                project_name2id=project_name2id,
            )
            service_account_name2id = service_account_runner.create_or_update_service_accounts(service_accounts, domain)

            # ### Region / zone / pool ###
            # Create Regions
            regions = domain_scenario.get("regions", [])
            rzp_runner = RegionZonePoolRunner(self.clients, update_mode=self.is_update_mode)
            region_name2id = rzp_runner.create_or_update_regions(regions, domain)

            zones = domain_scenario.get("zones", [])
            zone_name2id = rzp_runner.create_or_update_zones(zones, domain)

            pools = domain_scenario.get("pools", [])
            pool_name2id = rzp_runner.create_or_update_pools(pools, domain)

            # Secret
            secrets = domain_scenario.get("secrets", [])
            secret_runner = SecretRunner(
                self.clients,
                update_mode=self.is_update_mode,
                region_name2id=region_name2id,
                zone_name2id=zone_name2id,
                pool_name2id=pool_name2id,
                project_name2id=project_name2id,
                service_account_name2id=service_account_name2id,
            )
            secret_name2id = secret_runner.create_or_update_secrets(secrets, domain)

            # Secret Group (CLOUD-930)
            secret_group = domain_scenario.get("secret_group", {})
            secret_group_runner = SecretGroupRunner(
                self.clients,
                update_mode=self.is_update_mode,
                secret_name2id=secret_name2id
            )
            secret_group_name2id = secret_group_runner.create_or_update_secret_group(secret_group, domain)

            # inventory
            # inventory.ResourceGroup
            resource_group = domain_scenario.get("inventory.ResourceGroup", [])
            resource_group_runner = ResourceGroupRunner(
                self.clients,
                update_mode=self.is_update_mode,
                project_name2id=project_name2id
            )
            resource_group_name2id = resource_group_runner.create_or_update_resource_group(resource_group, domain)

            # inventory.Collector
            collectors = domain_scenario.get("collectors", [])
            collector_runner = CollectorRunner(
                self.clients,
                update_mode=self.is_update_mode,
                secret_name2id=secret_name2id,
                secret_group_name2id=secret_group_name2id,
                project_name2id=project_name2id
            )
            collector_runner.create_or_update_collectors(collectors, domain)

            is_collect = domain_scenario.get("is_collect", False)
            if is_collect:
                collector_runner.collect(domain)

            # Monitoring
            datasources = domain_scenario.get("monitoring.DataSource", [])
            datasource_runner = DataSourceRunner(
                self.clients,
                update_mode=self.is_update_mode
            )
            datasource_name2id = datasource_runner.register_or_update_datasources(datasources, domain)

            # statistics.Schedule
            schedules = domain_scenario.get("statistics.Schedule", [])
            schedule_runer = ScheduleRunner(
                self.clients,
                update_mode=self.is_update_mode
            )
            power_schedule_name2id = schedule_runer.add_or_update_schedules(schedules, domain)

            # power_scheduler.Schedule
            schedules = domain_scenario.get("power_scheduler.Schedule", [])
            schedule_runer = PowerScheduleRunner(
                self.clients,
                update_mode=self.is_update_mode,
                project_name2id = project_name2id
            )
            power_schedule_name2id = schedule_runer.add_or_update_schedules(schedules, domain)

        return domain

    @classmethod
    def _update_supervisor_token(cls, consul, token):
        cls._add_token(consul['host'], os.path.join(consul['env'], 'supervisor'), 'TOKEN', token)

    @classmethod
    def _update_token(cls, consul, key, token):
        cls._add_token(consul['host'], os.path.join(consul['env'], key), 'TOKEN', token)

    @classmethod
    def _update_domain_at_consul(cls, consul, key, value):
        cls._add_token(consul['host'], consul['env'], 'domain_id', value)

    @classmethod
    def _add_token(cls, endpoint, directory, key, value):
        """
        Args:
            endpoint: consul endpoint (ex. config.exmaple.com)
            directory: directory of Key/Value (ex. debug/supervisor)
            key: Key (ex. token)
            value: Value (ex. xxxxxsa2321323123123123312)
        """
        con = consul.Consul(host=endpoint)
        full_path = os.path.join(directory, key)

        con.kv.put(full_path, value)

    def update_consul(self, key, value):
        # This is for use of TestCase
        self._add_token(self.consul['host'], os.path.join(self.consul['env'], key), 'ID', value)
