# from spaceone.tester.scenario import Scenario

from spaceone.tester.scenario.runner.runner import ServiceRunner, print_json

__all__ = ['ScheduleRunner']


class ScheduleRunner(ServiceRunner):

    def __init__(self, clients, update_mode=False):
        self.set_clients(clients)
        self.update_mode = update_mode
        self.schedule_name2id = {}

    def add_or_update_schedules(self, schedules, domain):
        for schedule in schedules:
            if self.update_mode:
                schedule_obj = self._find_schedule(schedule, domain)
                if schedule_obj is None:
                    self._add_schedule(schedule, domain)
            else:
                self._add_schedule(schedule, domain)

        return self.schedule_name2id

    def _add_schedule(self, schedule, domain):
        schedule['domain_id'] = domain.domain_id
        schedule_obj = self.statistics.Schedule.add(schedule, metadata=self.get_meta())
        self.schedule_name2id[schedule_obj.topic] = schedule_obj.schedule_id
        self.append_terminator(
            self.statistics.Schedule.delete,
            {
                'schedule_id': schedule_obj.schedule_id,
                'domain_id': domain.domain_id
            }
        )
        print("########### add schedule #############")
        print_json(schedule_obj)
        return schedule_obj

    def _find_schedule(self, schedule, domain):
        param = {
            'topic': schedule['topic'],
            'domain_id': domain.domain_id
        }
        results = self.statistics.Schedule.list(param, metadata=self.get_meta())

        if len(results.results) >= 1:
            print(f'Found {len(results.results)} schedule(s).')
            return results.results[0]
        return None


