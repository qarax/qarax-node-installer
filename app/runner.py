import ansible_runner
import os
import shelve

from pprint import pprint

extra_vars = {
    'ansible_user': 'root',
    'fcversion': '1.4.1',
}


class AnsibleRunner:

    host_id_to_runner = {}

    def runner_process_messages(self, data):
        event = data['event']
        if event == 'playbook_on_task_start':
            pprint(data['event_data'])

    def run_playbook(self, host: str, role: str, password: str, host_id: str):
        playbook = {
            'hosts': 'all',
            'gather_facts': True,
            'roles': [role],
        }
        envvars = {
            'ANSIBLE_ROLES_PATH': os.path.join(os.path.dirname(__file__), 'playbooks/roles'),
        }
        hosts = {
            'hosts': {
                'host1': {
                    'ansible_host': host,
                },
            },
            'vars': {
                'ansible_user': 'root',
                'ansible_password': password,
            }
        }

        thread, runner = ansible_runner.run_async(
            playbook=[playbook],
            envvars=envvars,
            extravars=extra_vars,
            inventory={'all': hosts},
            event_handler=self.runner_process_messages)

        self.host_id_to_runner[host_id] = runner

    def get_runner_status(self, host_id: str):
        runner = self.host_id_to_runner.get(host_id)
        return runner.status if runner else None
