import re
from pathlib import Path
from typing import Literal

import yaml
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, field_validator

DATA_FILE = Path(__file__).resolve().parent.parent / "data" / "hosts.yaml"
STATIC_DIR = Path(__file__).resolve().parent.parent / "static"

HEADER = (
    "# Inventaire des hosts. Chaque entrée est déclarative : pas de base de données.\n"
    "# access: liste de protocoles/accès possibles (ssh, rdp, web, ...)\n"
)

IP_RE = re.compile(r"^\d{1,3}(\.\d{1,3}){3}$")


class Host(BaseModel):
    ip: str
    name: str
    type: Literal["physical", "virtual"]
    location: Literal["on-prem", "cloud"]
    access: list[str] = []

    @field_validator("ip")
    @classmethod
    def validate_ip(cls, value: str) -> str:
        if not IP_RE.match(value):
            raise ValueError("IP invalide")
        return value

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Nom requis")
        return value


def read_hosts() -> list[dict]:
    return yaml.safe_load(DATA_FILE.read_text()) or []


def write_hosts(hosts: list[dict]) -> None:
    body = yaml.safe_dump(hosts, sort_keys=False, allow_unicode=True)
    DATA_FILE.write_text(HEADER + body)


app = FastAPI(title="ipbb")


@app.get("/api/hosts", response_model=list[Host])
def list_hosts() -> list[Host]:
    return [Host(**entry) for entry in read_hosts()]


@app.post("/api/hosts", response_model=Host, status_code=201)
def create_host(host: Host) -> Host:
    hosts = read_hosts()
    if any(h["ip"] == host.ip for h in hosts):
        raise HTTPException(409, f"Un host existe déjà avec l'IP {host.ip}")
    hosts.append(host.model_dump())
    write_hosts(hosts)
    return host


@app.put("/api/hosts/{ip}", response_model=Host)
def update_host(ip: str, host: Host) -> Host:
    hosts = read_hosts()
    idx = next((i for i, h in enumerate(hosts) if h["ip"] == ip), None)
    if idx is None:
        raise HTTPException(404, f"Aucun host avec l'IP {ip}")
    if host.ip != ip and any(h["ip"] == host.ip for h in hosts):
        raise HTTPException(409, f"Un host existe déjà avec l'IP {host.ip}")
    hosts[idx] = host.model_dump()
    write_hosts(hosts)
    return host


app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")
