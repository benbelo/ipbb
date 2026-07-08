import csv
import io
import re
from pathlib import Path
from typing import Literal

import yaml
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, ValidationError, field_validator

DATA_FILE = Path(__file__).resolve().parent.parent / "data" / "hosts.yaml"
STATIC_DIR = Path(__file__).resolve().parent.parent / "static"

HEADER = (
    "# Inventaire des hosts. Chaque entrée est déclarative : pas de base de données.\n"
    "# type: vm, bare-metal, firewall, switch, ap ou iot\n"
    "# location: onprem-cachan, onprem-troyes, onprem-dijon, onprem-orleans, onprem-aix ou cloud-azure\n"
    "# vlan: optionnel, numérique\n"
    "# access: liste de protocoles/accès possibles (ssh, rdp, web, ...)\n"
)

IP_RE = re.compile(r"^\d{1,3}(\.\d{1,3}){3}$")
CSV_FIELDS = ["ip", "vlan", "name", "type", "location", "access"]


class Host(BaseModel):
    ip: str
    vlan: int | None = None
    name: str
    type: Literal["vm", "bare-metal", "firewall", "switch", "ap", "iot"]
    location: Literal[
        "onprem-cachan",
        "onprem-troyes",
        "onprem-dijon",
        "onprem-orleans",
        "onprem-aix",
        "cloud-azure",
    ]
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
    hosts.append(host.model_dump(exclude_none=True))
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
    hosts[idx] = host.model_dump(exclude_none=True)
    write_hosts(hosts)
    return host


@app.delete("/api/hosts/{ip}", status_code=204)
def delete_host(ip: str) -> None:
    hosts = read_hosts()
    remaining = [h for h in hosts if h["ip"] != ip]
    if len(remaining) == len(hosts):
        raise HTTPException(404, f"Aucun host avec l'IP {ip}")
    write_hosts(remaining)


@app.get("/api/hosts/export")
def export_hosts() -> Response:
    hosts = [Host(**entry) for entry in read_hosts()]
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=CSV_FIELDS)
    writer.writeheader()
    for h in hosts:
        writer.writerow(
            {
                "ip": h.ip,
                "vlan": h.vlan if h.vlan is not None else "",
                "name": h.name,
                "type": h.type,
                "location": h.location,
                "access": ";".join(h.access),
            }
        )
    return Response(
        content=buffer.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=hosts.csv"},
    )


@app.post("/api/hosts/import", response_model=list[Host])
def import_hosts(file: UploadFile = File(...)) -> list[Host]:
    text = file.file.read().decode("utf-8")
    reader = csv.DictReader(io.StringIO(text))

    hosts: list[Host] = []
    errors: list[str] = []
    seen_ips: set[str] = set()

    for i, row in enumerate(reader, start=2):
        try:
            host = Host(
                ip=(row.get("ip") or "").strip(),
                vlan=int(row["vlan"]) if row.get("vlan", "").strip() else None,
                name=(row.get("name") or "").strip(),
                type=(row.get("type") or "").strip(),
                location=(row.get("location") or "").strip(),
                access=[a.strip() for a in (row.get("access") or "").split(";") if a.strip()],
            )
        except (ValidationError, ValueError) as e:
            errors.append(f"Ligne {i}: {e}")
            continue
        if host.ip in seen_ips:
            errors.append(f"Ligne {i}: IP {host.ip} en double dans le fichier")
            continue
        seen_ips.add(host.ip)
        hosts.append(host)

    if errors:
        raise HTTPException(422, "; ".join(errors))

    write_hosts([h.model_dump(exclude_none=True) for h in hosts])
    return hosts


app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")
