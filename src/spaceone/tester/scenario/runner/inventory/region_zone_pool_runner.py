from spaceone.core.utils import random_string

from spaceone.tester.scenario.runner.runner import ServiceRunner, print_json

__all__ = ['RegionZonePoolRunner']


class RegionZonePoolRunner(ServiceRunner):

    def __init__(self, clients, update_mode=False):
        self.set_clients(clients)
        self.update_mode = update_mode
        self.project_name2pg_id = {}
        self.project_name2id = {}
        self.zone_name2id = {}
        self.region_name2id = {}
        self.pool_name2id = {}

    def create_or_update_regions(self, regions, domain):
        for region in regions:
            region_obj = None
            if self.update_mode:
                results = self._find_region(domain, region)
                if len(results.results) >= 1:
                    print(f'Found {len(results.results)} region(s).')
                    region_obj = self._update_region(region, results.results[0])

            if region_obj is None:
                print(f'Create a new region.')
                region_obj = self._create_region(region, domain)

            self.region_name2id[region_obj.name] = region_obj.region_id
        return self.region_name2id

        print(f'region_name2id: {self.region_name2id}')

    def create_or_update_zones(self, zones, domain):
        for zone in zones:
            zone_obj = None

            if self.update_mode:
                zone_obj = self._find_zone(zone, domain)
                if zone_obj:
                    zone_obj = self._update_zone(zone, zone_obj)

            if zone_obj is None:
                zone_obj = self._create_zone(zone, domain)

            region_name = zone['region']
            self.zone_name2id[region_name][zone_obj.name] = zone_obj.zone_id
        print(f'zone_name2id: {self.zone_name2id}')
        return self.zone_name2id

    def create_or_update_pools(self, pools, domain):
        for pool in pools:
            pool_obj = None
            if self.update_mode:
                # TODO: find pool
                pool_obj = self._find_pool(pool, domain)
                if pool_obj:
                    pool_obj = self._update_pool(pool, pool_obj)

            if pool_obj is None:
                pool_obj = self._create_pool(pool, domain)

            pool_name = pool_obj.name
            self.pool_name2id[pool_name] = pool_obj.pool_id

        print(f'pool_name2id: {self.pool_name2id}')
        return self.pool_name2id

    def _find_region(self, domain, region):
        query = {
            'domain_id': domain.domain_id,
            'query': {
                'filter': [{
                    'k': 'name', 'v': region['name'], 'o': 'eq'
                }]}
        }
        results = self.inventory.Region.list(
            query,
            metadata=self.get_meta()
        )
        return results

    def _update_region(self, region_param, region_obj):
        region_default_params = {
            'name': region_param['name'],
            'region_id': region_obj.region_id,
            'domain_id': region_obj.domain_id
        }
        region_default_params.update(region_param)

        region_obj = self.inventory.Region.update(
            region_default_params, metadata=self.get_meta()
        )
        print("########### Update Region ###############")
        print_json(region_obj)
        return region_obj

    def _create_region(self, region, domain):
        region_default_params = {
            'name': region.get('name', f'region-{random_string()[0:4]}'),
            'domain_id': domain.domain_id
        }
        region_default_params.update(region)

        region_obj = self.inventory.Region.create(
            region_default_params, metadata=self.get_meta()
        )
        print("########### Create Region ###############")
        print_json(region_obj)
        self.region_name2id[region_obj.name] = region_obj.region_id
        self.append_terminator(
            self.inventory.Region.delete, {'domain_id': domain.domain_id,
                                          'region_id': region_obj.region_id}
        )
        return region_obj

    def _find_zone(self, zone, domain):
        param = {
            'name': zone['name'],
            'domain_id': domain.domain_id
        }
        results = self.inventory.Zone.list(param, metadata=self.get_meta())
        if len(results.results) >= 1:
            print(f'Found {len(results.results)} zone(s).')
            return results.results[0]

        return None

    def _create_zone(self, zone, domain):
        region_name = zone['region']
        if self.zone_name2id.get(region_name) is None:
            self.zone_name2id[region_name] = {}
        region_id = self.region_name2id[region_name]
        zone_default_params = {
            'name': zone.get('name', f'zone-{random_string()[0:4]}'),
            'region_id': region_id,
            'domain_id': domain.domain_id
        }
        # del zone['region']
        zone_default_params.update(zone)
        del zone_default_params['region']
        zone_obj = self.inventory.Zone.create(zone_default_params, metadata=self.get_meta())

        print("########### Create Zone ###############")
        print_json(zone_obj)
        self.append_terminator(
            self.inventory.Zone.delete, {'domain_id': domain.domain_id,
                                        'zone_id': zone_obj.zone_id}
        )
        return zone_obj

    def _update_pool(self, pool, pool_obj):
        region_name = pool['region']
        # region_id = self.region_name2id[region_name]
        zone_name = pool['zone']
        zone_id = self.zone_name2id[region_name][zone_name]
        default_pool_params = {
            'name': pool['name'],
            'pool_id': pool_obj.pool_id,
            'domain_id': pool_obj.domain_id
        }
        default_pool_params.update(pool)
        del default_pool_params['region']
        del default_pool_params['zone']
        pool_obj = self.inventory.Pool.update(default_pool_params, metadata=self.get_meta())
        print("########### Update Pool ###############")
        print_json(pool_obj)

        return pool_obj

    def _find_pool(self, pool, domain):
        param = {
            'name': pool['name'],
            'domain_id': domain.domain_id
        }
        results = self.inventory.Pool.list(param, metadata=self.get_meta())

        if len(results.results) >= 1:
            print(f'Found {len(results.results)} pool(s).')
            return results.results[0]
        return None

    def _create_pool(self, pool, domain):
        region_name = pool['region']
        # region_id = self.region_name2id[region_name]
        zone_name = pool['zone']
        zone_id = self.zone_name2id[region_name][zone_name]
        default_pool_params = {
            'name': pool['name'],
            'zone_id': zone_id,
            'domain_id': domain.domain_id
        }
        del pool['region']
        del pool['zone']
        default_pool_params.update(pool)
        pool_obj = self.inventory.Pool.create(default_pool_params, metadata=self.get_meta())
        print("########### Create Pool ###############")
        print_json(pool_obj)
        self.append_terminator(
            self.inventory.Pool.delete, {'domain_id': domain.domain_id,
                                        'pool_id': pool_obj.pool_id}
        )
        return pool_obj

    def _update_zone(self, zone, zone_obj):
        region_name = zone['region']
        if self.zone_name2id.get(region_name) is None:
            self.zone_name2id[region_name] = {}
        # region_id = self.region_name2id[region_name]
        zone_default_params = {
            'name': zone.get('name', f'zone-{random_string()[0:4]}'),
            'zone_id': zone_obj.zone_id,
            'domain_id': zone_obj.domain_id
        }
        zone_default_params.update(zone)
        del zone_default_params['region']
        zone_obj = self.inventory.Zone.update(zone_default_params, metadata=self.get_meta())

        print("########### Update Zone ###############")
        print_json(zone_obj)
        return zone_obj
