import uuid
import os
import ansible_runner
import logging
import traceback
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, Any, Optional
import threading

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)


class AnsibleRunner:
    def __init__(self, max_concurrent_runs=10):
        self.runs = {}
        self.executor = ThreadPoolExecutor(max_workers=max_concurrent_runs)
        self.lock = threading.Lock()

    def runner_process_messages(self, data):
        event = data["event"]
        if event == "playbook_on_task_start":
            log.debug(data["event_data"])

    def run_playbook(
        self,
        host: str,
        playbook_name: str,
        extra_vars: Dict[str, Any],
        password: Optional[str] = None,
        ssh_key_path: Optional[str] = None,
    ) -> str:
        run_id = str(uuid.uuid4())
        current_dir = os.path.dirname(__file__)
        playbook_dir = os.path.join(current_dir, "playbooks")
        playbook_path = os.path.join(playbook_dir, f"{playbook_name}.yaml")

        log.debug(f"Current directory: {current_dir}")
        log.debug(f"Playbook directory: {playbook_dir}")
        log.debug(f"Looking for playbook at: {playbook_path}")

        playbook_path = os.path.join(
            os.path.dirname(__file__), "playbooks", f"{playbook_name}.yaml"
        )
        if not os.path.exists(playbook_path):
            raise FileNotFoundError(
                f"Playbook {playbook_name} not found at {playbook_path}"
            )

        inventory = {
            "all": {
                "hosts": {
                    "target_host": {
                        "ansible_host": host,
                        "ansible_user": "root",
                    }
                }
            }
        }

        if password:
            inventory["all"]["hosts"]["target_host"]["ansible_password"] = password
        elif ssh_key_path:
            inventory["all"]["hosts"]["target_host"][
                "ansible_ssh_private_key_file"
            ] = ssh_key_path
        else:
            raise ValueError("Either password or ssh_key_path must be provided")

        future = self.executor.submit(
            self._run_playbook, run_id, playbook_path, inventory, extra_vars
        )
        self.runs[run_id] = {
            "status": "PENDING",
            "future": future,
        }

        return run_id

    def _run_playbook(
        self, run_id: str, playbook_path: str, inventory: Dict, extra_vars: Dict
    ):
        log.info(f"_run_playbook started for run_id: {run_id}")

        try:
            log.debug(f"Inventory: {inventory}")
            log.debug(f"Extra vars: {extra_vars}")

            with self.lock:
                self.runs[run_id]["status"] = "RUNNING"

            r = ansible_runner.run(
                playbook=playbook_path,
                inventory=inventory,
                extravars=extra_vars,
                quiet=False,
            )
            log.debug(
                f"ansible_runner completed for run ID: {run_id}. Status: {r.status}"
            )
            with self.lock:
                self.runs[run_id]["result"] = r
                self.runs[run_id]["status"] = (
                    "COMPLETED" if r.status == "successful" else "FAILED"
                )
        except Exception as e:
            log.error(
                f"Error in ansible_runner for run ID: {run_id}. Error: {str(e)}",
                exc_info=True,
            )
            with self.lock:
                self.runs[run_id]["status"] = "ERROR"
                self.runs[run_id]["error"] = str(e)

    def event_handler(self, event):
        log.debug(f"Ansible event: {event}")

    def get_status(self, run_id: str) -> Dict[str, Any]:
        if run_id not in self.runs:
            return {"status": "NOT_FOUND"}

        run = self.runs[run_id]
        status = run["status"]

        if status == "COMPLETED":
            result = run["result"]
            return {
                "status": status,
                "stats": result.stats,
                "host_status": result.status,
            }
        elif status == "FAILED":
            result = run["result"]
            return {
                "status": status,
                "stats": result.stats,
                "host_status": result.status,
            }
        elif status == "ERROR":
            return {"status": status, "error": run.get("error", "Unknown error")}
        else:
            return {"status": status}

    def get_all_statuses(self) -> Dict[str, str]:
        return {run_id: run["status"] for run_id, run in self.runs.items()}
