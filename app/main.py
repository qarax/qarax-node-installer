from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Optional
from .runner import AnsibleRunner

app = FastAPI()
runner = AnsibleRunner()

class PlaybookParams(BaseModel):
    host: str
    playbook_name: str
    extra_vars: Dict[str, str]
    password: Optional[str]
    ssh_key_path: Optional[str]

@app.post("/run_playbook")
async def run_playbook(params: PlaybookParams):
    try:
        run_id = runner.run_playbook(
            params.host,
            params.playbook_name,
            params.extra_vars,
            params.password,
            params.ssh_key_path
        )
        return {"run_id": run_id}
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Playbook not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/status/{run_id}")
async def get_status(run_id: str):
    status = runner.get_status(run_id)
    if status['status'] == 'NOT_FOUND':
        raise HTTPException(status_code=404, detail="Run ID not found")
    return status

@app.get("/statuses")
async def get_all_statuses():
    return runner.get_all_statuses()

@app.post("/cancel/{run_id}")
async def cancel_run(run_id: str):
    if runner.cancel_run(run_id):
        return {"message": "Run cancelled successfully"}
    else:
        raise HTTPException(status_code=400, detail="Unable to cancel run")

@app.post("/cleanup")
async def cleanup_completed_runs():
    runner.cleanup_completed_runs()
    return {"message": "Cleanup completed"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)