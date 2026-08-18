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

Deux pipelines GitHub Actions :

| Pipeline | Déclencheur | Rôle |
|---|---|---|
| **CI** | toute branche et Pull Request | Tests unitaires, build du frontend, construction des images |
| **CD** | `main` | Publication des images sur GitHub Container Registry, déploiement et tests de recette |

Stratégie de branches : `feature/*` → `develop` → `main`.

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
