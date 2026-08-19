# EventHub

> Plateforme de gestion des événements académiques et culturels du
> **Dakar Institute of Technology**.

Projet d'examen pratique DevOps — Master 1 Intelligence Artificielle — Équipe 6.

---

## Le projet

Le DIT organise régulièrement des conférences, ateliers et séminaires. Leur
gestion reposait jusqu'ici sur des outils dispersés — Google Forms, Excel,
emails — ce qui rendait difficile le suivi des inscriptions en temps réel et
privait les organisateurs d'une vision d'ensemble.

EventHub réunit tout cela dans une plateforme unique qui permet de :

- créer et gérer des événements (titre, date, lieu, capacité) ;
- gérer les comptes des participants ;
- inscrire des participants et annuler leurs inscriptions ;
- suivre en temps réel les places restantes et les statistiques.

L'application est construite en **architecture microservices**, entièrement
conteneurisée, et déployée automatiquement.

---

## Architecture

```
                    Navigateur
                        │
                        ▼  :8080
              ┌───────────────────┐
              │      GATEWAY      │  seul point d'entrée
              └─────────┬─────────┘
                        │
      ┌───────┬─────────┼──────────────┬──────────────┐
      ▼       ▼         ▼              ▼              ▼
  frontend  events  participants  registrations
  (Angular)  :8001     :8002          :8003
                                        │
      └───────┴─────────┴───────────────┘
                        │
                        ▼
                   PostgreSQL
              (3 bases indépendantes)
```

| Service | Rôle |
|---|---|
| `gateway` | Point d'entrée unique, routage vers le frontend et les API |
| `frontend` | Interface web |
| `events-service` | Événements et disponibilité des places |
| `participants-service` | Comptes participants |
| `registrations-service` | Inscriptions, appelle les deux autres services |
| `postgres` | Base de données, une par microservice |

---

## Structure du projet

```
eventhub/
├── events-service/          Microservice Événements
├── participants-service/    Microservice Participants
├── registrations-service/   Microservice Inscriptions
├── frontend/                Application Angular
├── gateway/                 Reverse proxy Nginx
├── infra/postgres/init/     Création des bases au démarrage
├── scripts/                 Tests de recette
├── .github/workflows/       Pipelines CI et CD
├── docker-compose.yml       Orchestration
└── Makefile                 Raccourcis de commandes
```

Chaque microservice suit la même organisation interne :

```
<service>/
├── app/          Code de l'application
├── tests/        Tests unitaires
├── Dockerfile
└── requirements.txt
```

---

## Prérequis

- **Docker** 24+ et **Docker Compose** v2
- **Git**

Pour développer hors conteneur : Python 3.12 et Node.js 20.

---

## Lancer le projet

### Avec Docker Compose (recommandé)

```bash
git clone https://github.com/dioufra/eventhub.git
cd eventhub

cp .env.example .env      # puis renseignez POSTGRES_PASSWORD
docker compose up -d
```

Attendez que les six conteneurs soient sains :

```bash
docker compose ps
```

L'application est disponible sur **http://localhost:8080**

Pour arrêter :

```bash
docker compose down          # conserve les données
docker compose down -v       # supprime aussi la base de données
```

### Avec Docker, service par service

Sans Docker Compose, chaque image se construit et se lance à la main. Les
conteneurs doivent porter **exactement ces noms** : ce sont eux que le DNS
interne de Docker résout, et que la passerelle utilise pour router les appels.

```bash
# 1. Un réseau commun à tous les conteneurs
docker network create eventhub-net

# 2. La base de données, avec le script qui crée les trois bases
docker run -d --name postgres --network eventhub-net \
  -e POSTGRES_USER=eventhub \
  -e POSTGRES_PASSWORD=motdepasse \
  -e POSTGRES_DB=postgres \
  -v eventhub-pgdata:/var/lib/postgresql/data \
  -v "$PWD/infra/postgres/init:/docker-entrypoint-initdb.d:ro" \
  postgres:16-alpine

# 3. Construction des cinq images
docker build -t eventhub-events        ./events-service
docker build -t eventhub-participants  ./participants-service
docker build -t eventhub-registrations ./registrations-service
docker build -t eventhub-frontend      ./frontend
docker build -t eventhub-gateway       ./gateway

# 4. Les trois microservices
docker run -d --name events-service --network eventhub-net \
  -e DATABASE_URL="postgresql+pg8000://eventhub:motdepasse@postgres:5432/eventhub_events" \
  eventhub-events

docker run -d --name participants-service --network eventhub-net \
  -e DATABASE_URL="postgresql+pg8000://eventhub:motdepasse@postgres:5432/eventhub_participants" \
  eventhub-participants

docker run -d --name registrations-service --network eventhub-net \
  -e DATABASE_URL="postgresql+pg8000://eventhub:motdepasse@postgres:5432/eventhub_registrations" \
  -e EVENTS_SERVICE_URL="http://events-service:8001" \
  -e PARTICIPANTS_SERVICE_URL="http://participants-service:8002" \
  eventhub-registrations

# 5. Le frontend, puis la passerelle qui expose l'ensemble
docker run -d --name frontend --network eventhub-net eventhub-frontend
docker run -d --name gateway  --network eventhub-net -p 8080:80 eventhub-gateway
```

L'application est disponible sur **http://localhost:8080**

> La passerelle résout le nom de ses cibles à son démarrage : lancez-la
> **après** le frontend et les trois microservices, sinon elle s'arrête sur
> `host not found in upstream`.

Pour tout arrêter et nettoyer :

```bash
docker rm -f gateway frontend registrations-service participants-service events-service postgres
docker network rm eventhub-net
docker volume rm eventhub-pgdata      # supprime aussi les données
```

### Avec le Makefile

```bash
make init     # crée le .env
make up       # démarre tout
make ps       # état des conteneurs
make logs     # suit les logs
make down     # arrête
make help     # liste toutes les commandes
```

### Sans Docker

Chaque microservice se lance indépendamment. PostgreSQL doit être démarré et
les trois bases créées au préalable.

```bash
cd events-service
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --port 8001
```

Répétez pour `participants-service` (port 8002) et `registrations-service`
(port 8003), puis lancez le frontend :

```bash
cd frontend
npm install --legacy-peer-deps
npm start                    # http://localhost:4200
```

---

## Adresses utiles

| | URL |
|---|---|
| Application | http://localhost:8080 |
| Documentation API — Événements | http://localhost:8001/docs |
| Documentation API — Participants | http://localhost:8002/docs |
| Documentation API — Inscriptions | http://localhost:8003/docs |

> Le port de l'application se règle avec `GATEWAY_PORT` dans le fichier `.env`.

---

## Tests

```bash
make test     # tests unitaires des trois microservices
make smoke    # tests de recette sur l'application démarrée
```

---

## Intégration et déploiement continus

Deux pipelines GitHub Actions, définis dans `.github/workflows/`.

### `ci.yml` — à chaque push et Pull Request

| Étape | Ce qu'elle fait |
|---|---|
| Configuration | Valide `docker-compose.yml`, vérifie qu'un seul port est publié en production et que le script d'initialisation crée bien trois bases |
| Tests backend | `pytest` sur les trois microservices, exécutés **en parallèle** |
| Frontend | Installation, compilation de production, vérification du chemin de sortie du build |
| Images | Construction des cinq images Docker, sans publication |

Chaque étape vérifie d'abord si son périmètre est implémenté : un dossier
encore vide est signalé et ignoré plutôt que de faire échouer le pipeline.

### `cd.yml` — à chaque fusion sur `main`

| Étape | Ce qu'elle fait |
|---|---|
| Tests | Rejeu des tests unitaires — on ne publie jamais sans revalider |
| Publication | Les cinq images sont poussées sur **GitHub Container Registry**, étiquetées `latest` et `sha-<commit>` |
| Déploiement | La pile est démarrée à partir des images publiées |
| Recette | 27 contrôles de bout en bout sur l'application déployée |

L'étiquette `sha-<commit>` permet de savoir exactement quel code correspond à
une image donnée.

### Stratégie de branches

```
feature/*  ──▶  develop  ──▶  main
(développement)  (intégration)  (production)
```

Aucun commit n'est poussé directement sur `main` : tout passe par une Pull
Request relue.

---

## Technologies

| Domaine | Choix |
|---|---|
| Backend | FastAPI (Python 3.12), SQLAlchemy |
| Frontend | Angular 20 |
| Base de données | PostgreSQL 16 |
| Reverse proxy | Nginx |
| Conteneurisation | Docker, Docker Compose |
| CI/CD | GitHub Actions, GitHub Container Registry |

---

## Auteurs — Équipe 6

Master 1 Intelligence Artificielle · Dakar Institute of Technology

| Nom | Rôle | GitHub |
|---|---|---|
| **DIOUF François Pape** | Scrum Master | [@dioufra](https://github.com/dioufra) |
| **Mohamed Sow** | Développeur | [@sultan2096](https://github.com/sultan2096) |
| **Berly Lora** | Développeur | [@loraham057-spec](https://github.com/loraham057-spec) |
| **Kra Junior** | Développeur | [@KraJunior](https://github.com/KraJunior) |
| **Aichatou Ndaw** | Développeur | [@chattoundaw26-tech](https://github.com/chattoundaw26-tech) |

---

<sub>Août 2026 — Examen pratique DevOps, Dakar Institute of Technology.</sub>
