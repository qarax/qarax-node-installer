from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional, Dict, Any
from .runner import AnsibleRunner

app = FastAPI()
runner = AnsibleRunner()

class PlaybookParams(BaseModel):
    host: str
    playbook_name: str
    extra_vars: Dict[str, Any]
    password: Optional[str] = None
    ssh_key_path: Optional[str] = None

@app.post("/run_playbook")
async def run_playbook(params: PlaybookParams):
    run_id = await runner.run_playbook(
        host=params.host,
        playbook_name=params.playbook_name,
        extra_vars=params.extra_vars,
        password=params.password,
        ssh_key_path=params.ssh_key_path,
    )
    return {"run_id": run_id}

@app.get("/run_status/{run_id}")
def get_run_status(run_id: str):
    status = runner.get_status(run_id)
    return status
