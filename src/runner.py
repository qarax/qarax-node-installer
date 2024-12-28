import uuid
import os
import ansible_runner
import logging
import asyncio
from typing import Dict, Any, Optional

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)

class AnsibleRunner:
    def __init__(self):
        self.runs = {}
        self.lock = asyncio.Lock()
        current_dir = os.path.dirname(__file__)
        self.project_root = os.path.dirname(current_dir)

    async def run_playbook(
        self,
        host: str,
        playbook_name: str,
        extra_vars: Dict[str, Any],
        password: Optional[str] = None,
        ssh_key_path: Optional[str] = None,
    ) -> str:
        run_id = str(uuid.uuid4())

        playbook_dir = os.path.join(self.project_root, "playbooks")
        playbook_path = os.path.join(playbook_dir, f"{playbook_name}.yaml")

        log.debug(f"Project root: {self.project_root}")
        log.debug(f"Playbook directory: {playbook_dir}")
        log.debug(f"Looking for playbook at: {playbook_path}")

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

        async with self.lock:
            self.runs[run_id] = {
                "status": "PENDING",
            }

        asyncio.create_task(
            self._run_playbook(run_id, playbook_path, inventory, extra_vars)
        )

        return run_id

    async def _run_playbook(
        self, run_id: str, playbook_path: str, inventory: Dict, extra_vars: Dict
    ):
        log.info(f"_run_playbook started for run_id: {run_id}")

        try:
            log.debug(f"Inventory: {inventory}")
            log.debug(f"Extra vars: {extra_vars}")

            async with self.lock:
                self.runs[run_id]["status"] = "RUNNING"

            loop = asyncio.get_running_loop()
            r = await loop.run_in_executor(
                None,  # Use default executor
                lambda: ansible_runner.run(
                    private_data_dir=None,
                    playbook=playbook_path,
                    inventory=inventory,
                    extravars=extra_vars
                )
            )

            log.debug(
                f"ansible_runner completed for run ID: {run_id}. Status: {r.status}"
            )
            async with self.lock:
                self.runs[run_id]["result"] = r
                self.runs[run_id]["status"] = (
                    "COMPLETED" if r.status == "successful" else "FAILED"
                )
        except Exception as e:
            log.error(
                f"Error in ansible_runner for run ID: {run_id}. Error: {str(e)}",
                exc_info=True,
            )
            async with self.lock:
                self.runs[run_id]["status"] = "ERROR"
                self.runs[run_id]["error"] = str(e)

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
