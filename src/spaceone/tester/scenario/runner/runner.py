import logging
import pprint

from google.protobuf.json_format import MessageToDict

terminate_list = []
delete_list = []
meta = []
project_name2pg_id = {}

_LOGGER = logging.getLogger(__name__)


class ServiceRunner(object):

    def set_clients(self, clients):
        for client_name, client in clients.items():

            print(f'[set_clients] client_name: {client_name}')
            setattr(self, client_name, client)

    def set_meta(self, token):
        meta.append(('token', token))

    def get_meta(self):
        return meta

    def append_terminator(self, method, param):
        """
        Args:
            method: <service>.<API class>.<method> ex) repository.Repository.deregister
            param: param
        """
        try:
            terminate_list.append((method, param))
        except Exception as e:
            _LOGGER.debug(f'[delete] METHOD_DIC[{method}] not found')

    def append_delete(self, method, param):
        """
        Args:
            method: <service>.<API class>.<method> ex) repository.Repository.deregister
            param: param
        """
        try:
            delete_list.append((method, param))
        except Exception as e:
            _LOGGER.debug(f'[delete] METHOD_DIC[{method}] not found')

    @classmethod
    def terminate(cls):
        # print(terminate_list)
        # print(meta)
        for args in reversed(terminate_list):
            try:
                method, param = args
                _LOGGER.debug(f'[terminate] param: {param}')
                print(f'[terminate] param: {param}')
                method(param, metadata=meta)
            except Exception as e:
                print(f"fail to call method: {args}")
                _LOGGER.error(f"fail to call method: {args}")
        del terminate_list[:]

    @classmethod
    def delete(cls):
        for args in reversed(delete_list):
            try:
                method, param = args
                # _LOGGER.debug(f'[tearDown] param: {param}')
                method(param, metadata=meta)
            except Exception as e:
                _LOGGER.error(f"fail to call method: {args}")
        # clean list
        del delete_list[:]

def to_json(msg):
    return MessageToDict(msg, preserving_proto_field_name=True)


def print_json(msg):
    if msg:
        pprint.pprint(to_json(msg))
        print("")
    else:
        print("Something wrong: %s" % type(msg))
        print(msg)
