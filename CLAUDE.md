# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Objectif

Une appli web simple et minimaliste, dans l'esprit de phpipam mais simplifiée et plus jolie visuellement.
Peu importe la stack technique utilisée.

## Contraintes

- Pas de base de données : tout est déclaratif, stocké en YAML.
- Doit être dockerisable.
- Doit pouvoir être publiée sur GitHub.
- Exposée derrière un reverse-proxy Traefik. La restriction d'accès n'est pas encore définie, mais
  éviter tout système d'authentification lourd.
- Doit gérer l'affichage, le filtrage et le tri d'environ 200 hosts (40 VMs, 5 firewalls, des switchs
  et des APs).

## Champs affichés par host

- IP
- Nom (friendly-name)
- Type : physique ou virtuel (VM ou bare-metal)
- Emplacement : on-prem ou cloud
- Accès possibles (RDP, SSH, web, …)

## Stack

- Backend : Python / FastAPI. Sert l'API et les fichiers statiques (pas de build JS, pas de templating).
- Frontend : HTML/CSS/JS vanilla dans `static/`. Filtrage et tri se font entièrement côté client
  (~200 lignes, pas besoin d'aller-retour serveur).
- Données : `data/hosts.yaml`, chargé à chaque requête vers `/api/hosts` (pas de cache, pas de bdd).

## Commandes

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload   # dev, http://localhost:8000

docker build -t ipbb .
docker run -p 8000:8000 -v $(pwd)/data:/app/data:ro ipbb
```

## Architecture

- `app/main.py` : unique module backend. Modèle `Host` (pydantic) avec validation stricte des champs
  `type` (`physical`/`virtual`) et `location` (`on-prem`/`cloud`). `/api/hosts` relit et parse le YAML
  à chaque appel. Les fichiers statiques sont montés à la racine (`/`) via `StaticFiles`.
- `static/app.js` : récupère `/api/hosts` une fois au chargement, garde l'état en mémoire (`hosts`),
  puis toute interaction (recherche, filtres, tri par colonne) ne fait que refiltrer/retrier ce
  tableau en JS et ré-afficher le `<tbody>` — aucune requête réseau supplémentaire.
- `data/hosts.yaml` : seule source de vérité. Éditer ce fichier à la main pour ajouter/modifier des
  hosts ; pas de migration ni de schéma séparé, la validation est faite par le modèle `Host`.
- `docker-compose.yml` : suppose un réseau externe `traefik` déjà créé (`docker network create
  traefik`) et un routage par `Host()` — aucune authentification n'est en place, à ajouter si besoin
  (ex. middleware Traefik forward-auth) sans en faire porter la complexité à l'appli elle-même.
