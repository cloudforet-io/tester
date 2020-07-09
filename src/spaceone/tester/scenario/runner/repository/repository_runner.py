# from spaceone.tester.scenario import Scenario

from spaceone.tester.scenario.runner.runner import ServiceRunner, print_json

__all__ = ['RepositoryRunner']


class RepositoryRunner(ServiceRunner):

    def __init__(self, clients, update_mode=False):
        self.set_clients(clients)
        self.update_mode = update_mode

    def register_local_repository(self, param):
        if param:
            repo = self.repository.Repository.register(param, metadata=self.get_meta())
            self.append_terminator(self.repository.Repository.deregister, {'repository_id': repo.repository_id})
            print_json(repo)
            return repo
        return None

    def register_remote_repositories(self, remote_repos, domain):
        for remote_repo in remote_repos:
            repo = self._register_remote_repository(remote_repo, domain)
            print_json(repo)

    def _register_remote_repository(self, param, domain):
        # Remote repo needs secret token
        token_name = param['secret_id']
        token = param[token_name]
        token['domain_id'] = domain.domain_id

        secret_info = self.secret.Secret.create(token, metadata=self.get_meta())
        secret_id = secret_info.secret_id
        self.append_terminator(
            self.secret.Secret.delete,
            {'secret_id': secret_id, 'domain_id': domain.domain_id}
        )

        param['secret_id'] = secret_id
        del param[token_name]

        repo = self.repository.Repository.register(param, metadata=self.get_meta())
        self.append_terminator(
            self.repository.Repository.deregister,
            {'repository_id': repo.repository_id}
        )

        return repo
