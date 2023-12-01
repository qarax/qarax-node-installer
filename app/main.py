from .runner import AnsibleRunner
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

runner = AnsibleRunner()


class PlaybookParams(BaseModel):
    role: str
    host: str
    password: str
    host_id: str


@app.get("/")
async def root():
    return {"message": "Hello World11"}


@app.post("/run/")
async def run(params: PlaybookParams):
    runner.run_playbook(params.host, params.role,
                        params.password, params.host_id)


@app.get("/status/{host_id}")
async def status(host_id):
    return runner.get_runner_status(host_id)
