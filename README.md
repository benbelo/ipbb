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

Ou avec `docker-compose.yml` (expose le port 8000 sur l'hôte, à brancher sur un Traefik externe si besoin) :

```bash
docker compose up -d --build
```

## Éditer l'inventaire

Utiliser l'UI directement ou à la main en modifiant `data/hosts.yaml`. Chaque host :

```yaml
- ip: 10.0.0.1
  name: srv-web01
  type: virtual        # virtual | physical
  location: on-prem    # on-prem | cloud
  access: [ssh, web]
```

## Export / import CSV

Le bouton "Export CSV" télécharge tout l'inventaire. Le bouton "Import CSV" remplace l'intégralité
des hosts par le contenu du fichier importé (utile pour éditer en masse dans un tableur). Colonnes
attendues : `ip,vlan,name,type,location,access` (les accès sont séparés par `;`).
