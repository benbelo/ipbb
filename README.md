# ipbb

Appli web simple pour lister/filtrer/trier un inventaire d'IPs (VMs, firewalls, switchs, APs), à la
phpipam mais simplifiée. Pas de base de données : tout est déclaratif dans `data/hosts.yaml`.

## Lancer en local

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Puis ouvrir http://localhost:8000.

## Lancer avec Docker

```bash
docker build -t ipbb .
docker run -p 8000:8000 -v $(pwd)/data:/app/data ipbb
```

Ou avec `docker-compose.yml` (pensez à créer le réseau externe `traefik` si besoin :
`docker network create traefik`).

## Éditer l'inventaire

Modifier `data/hosts.yaml`. Chaque host :

```yaml
- ip: 10.0.0.1
  name: srv-web01
  type: virtual        # virtual | physical
  location: on-prem    # on-prem | cloud
  access: [ssh, web]
```
