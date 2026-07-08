from pathlib import Path
from typing import Literal

import yaml
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

DATA_FILE = Path(__file__).resolve().parent.parent / "data" / "hosts.yaml"
STATIC_DIR = Path(__file__).resolve().parent.parent / "static"


class Host(BaseModel):
    ip: str
    name: str
    type: Literal["physical", "virtual"]
    location: Literal["on-prem", "cloud"]
    access: list[str] = []


app = FastAPI(title="ipbb")


@app.get("/api/hosts", response_model=list[Host])
def list_hosts() -> list[Host]:
    raw = yaml.safe_load(DATA_FILE.read_text()) or []
    return [Host(**entry) for entry in raw]


app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")
