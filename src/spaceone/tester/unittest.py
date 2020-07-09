import logging
import os
import pprint
import traceback
import unittest

from spaceone.core import config
from spaceone.core import pygrpc
from google.protobuf.json_format import MessageToDict

from spaceone.tester.scenario.scenario import Scenario

_LOGGER = logging.getLogger(__name__)
_LOGGER.setLevel(logging.DEBUG)

def to_json(msg):
    return MessageToDict(msg, preserving_proto_field_name=True)


def print_json(msg):
    if msg:
        pprint.pprint(to_json(msg))
        print("")
    else:
        print("Something wrong: %s" % type(msg))
        print(msg)


def _guess_version(endpoints):
    for (endpoint, v) in endpoints.items():
        for (k, v) in v.items():
            return k
    return "v1"


class TestCase(unittest.TestCase):
    config_uri = os.environ.get("TEST_CONFIG", "config.yml")  # YAML
    scenario_uri = os.environ.get("TEST_SCENARIO", "scenario.json")  # JSON
    scenario_params = os.environ.get("TEST_SCENARIO_PARAMS", "")
    terminate_list = []  # created list (api class object, {param for deletion})
    delete_list = []  # tearDown elements
    # terminated = False
    scenario = {}
    # is_update_mode = False
    scenario_obj = None

    # internal info at domain
    project_name2pg_id = {}  # Project name: project_group_id
    project_name2id = {}  # Project name: project_id
    region_name2id = {}
    zone_name2id = {}
    credential_name2id = {}

    @classmethod
    def setUpClass(cls):
        try:
            cls.config = config.load_config(cls.config_uri)
            endpoints = cls.config.get('ENDPOINTS', {})
            # version = 'v1'
            version = _guess_version(endpoints)
            # Create client of endpoints
            cls.client = {}
        except Exception as e:
            print(e)
            _LOGGER.warning(f'SKIP Load config')
            endpoints = {}

        for (endpoint, v) in endpoints.items():
            try:
                cls.client[endpoint] = pygrpc.client(endpoint=v.get(version),
                                                     version=version)
                setattr(cls, endpoint, cls.client[endpoint])
                _LOGGER.debug(f"Initialize {endpoint}")
            except Exception as e:
                _LOGGER.error(f"Fail to connector: {endpoint}")
                _LOGGER.error(e)

        try:
            cls.scenario_obj = Scenario(cls.scenario_uri, cls.client, cls.scenario_params)
            cls.domain = cls.scenario_obj.run_scenario()
            cls.meta = cls.scenario_obj.get_meta()

        except Exception as e:
            traceback.print_exc()

    @classmethod
    def tearDownClass(cls):

        for args in reversed(cls.terminate_list):
            try:
                method, param = args
                _LOGGER.debug(f'[tearDownClass] param: {param}')
                method(param, metadata=cls.meta)
            except Exception as e:
                _LOGGER.error(f"fail to call method: {args}")
        del cls.terminate_list[:]

        if cls.scenario_obj and cls.scenario_obj.is_terminate:
            _LOGGER.debug("\n\n######### TearDownClass - Run Terminate ###########")
            cls.scenario_obj.terminate()

    def tearDown(self):

        for args in reversed(self.delete_list):
            try:
                method, param = args
                #_LOGGER.debug(f'[tearDown] param: {param}')
                method(param, metadata=self.meta)
            except Exception as e:
                _LOGGER.error(f"fail to call method: {args}")
        # clean list
        del self.delete_list[:]

        if self.scenario_obj and self.scenario_obj.is_terminate:
            _LOGGER.debug("######### TearDown - Run Delete ###########")
            self.scenario_obj.delete()


    #########################
    # This is for API test
    #########################
    @classmethod
    def terminate(cls, method, param):
        """
        Args:
            method: <service>.<API class>.<method> ex) repository.Repository.deregister
            param: param
        """
        try:
            cls.terminate_list.append((method, param))
        except Exception as e:
            _LOGGER.debug(f'[delete] METHOD_DIC[{method}] not found')


    @classmethod
    def delete(cls, method, param):
        """
        Args:
            method: <service>.<API class>.<method> ex) repository.Repository.deregister
            param: param
        """
        try:
            cls.delete_list.append((method, param))
        except Exception as e:
            _LOGGER.debug(f'[delete] METHOD_DIC[{method}] not found')

