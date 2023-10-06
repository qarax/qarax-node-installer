import ansible_runner
import os

from pprint import pprint

extra_vars = {
    'ansible_user': 'root',
    'fcversion': '1.4.1',
}

class AnsibleRunner:
    def runner_process_messages(self, data):
        event = data['event']
        if event == 'playbook_on_task_start':
            pprint(data['event_data'])

    def run_playbook(self, host: str, role: str):
        playbook = {
            'hosts': 'all',
            'gather_facts': True,
            'roles': [role],
        }
        envvars = {
            'ANSIBLE_ROLES_PATH': os.path.join(os.path.dirname(__file__),'playbooks/roles'),
        }
        hosts = {
            'hosts':{
                'host1':{
                    'ansible_host': host,
                },
            },
            'vars':{
                'ansible_user': 'root',
                'ansible_password': 'centos',
            }
        }
        thread, r = ansible_runner.run_async(
            playbook=[playbook],
            envvars=envvars,
            extravars=extra_vars,
            inventory={'all': hosts},
            event_handler=self.runner_process_messages)

r = AnsibleRunner()
r.run_playbook()
