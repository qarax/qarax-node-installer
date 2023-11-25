from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

class PlaybookParams(BaseModel):
    role: str
    host: str
    password: str

@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.post("/run/")
async def run(params :PlaybookParams):
    from .runner import AnsibleRunner
    runner = AnsibleRunner()
    runner.run_playbook(params.host, params.role, params.password)