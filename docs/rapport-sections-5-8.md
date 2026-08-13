# Rapport EventHub — Sections 5 à 8

## 5. CI/CD avec GitHub Actions

Le pipeline CI/CD est défini dans `.github/workflows/ci.yml`. Il se déclenche sur toutes les branches `feature/*`, `develop` et les pull requests vers `develop` ou `main`. Le fichier `main` dispose d’un pipeline de déploiement continu (CD) complémentaire.

### Architecture du pipeline

Le workflow est divisé en quatre jobs qui s’exécutent en parallèle après l’étape de vérification :

1. **`compose`** : validation de la configuration Docker Compose.
   - Vérifie que `docker-compose.yml` est non vide et syntaxiquement valide.
   - Contrôle qu’un seul port est publié (celui de la gateway en architecture B).
   - Vérifie que le script d’initialisation PostgreSQL crée bien les trois bases de données.

2. **`backend`** : tests unitaires des trois microservices.
   - Utilise une matrice pour exécuter les tests de `events-service`, `participants-service` et `registrations-service`.
   - Installe Python 3.12, crée un environnement virtuel, installe `requirements-dev.txt` et lance `pytest -v`.
   - Ignore silencieusement les services non encore implémentés grâce à une vérification de taille des fichiers.

3. **`frontend`** : build Angular.
   - Utilise Node.js 20 et `npm ci`.
   - Compile en mode production et vérifie que le fichier `dist/frontend/browser/index.html` est généré.

4. **`images`** : construction des images Docker.
   - Utilise `docker/setup-buildx-action` et `docker/build-push-action`.
   - Construit les images des services, du frontend et de la gateway en local (`push: false`), avec cache GitHub Actions.

### Choix techniques

- **GitHub-hosted runners** (`ubuntu-latest`) : homogénéité et pas de maintenance.
- **Matrice de services** : isole les échecs et accélère le feedback.
- **Vérification conditionnelle** : permet de fusionner le workflow dès le début du projet, même si tous les services ne sont pas encore codés.
- **Cache pip / npm / Buildx** : réduit le temps d’exécution.

### Déploiement continu (CD)

Le workflow CD, bien que non livré en intégralité ici, repose sur la même structure : après validation sur `develop`, un merge sur `main` déclenche le build, la publication des images sur Docker Hub ou GHCR, et le déploiement automatique sur l’environnement cible.

---

## 6. Interface Frontend

L’interface utilisateur est développée en **Angular** et servie par un conteneur **Nginx**. Aucun port n’est exposé directement par le frontend ; c’est la **gateway Nginx** qui route le trafic externe vers `frontend:80` pour toutes les requêtes ne correspondant pas à un chemin `/api/*`.

### Structure des écrans

Le frontend est organisé en modules fonctionnels :

- **Événements** : liste filtrable, création, modification, suppression, détails, places restantes.
- **Participants** : création de compte, profil, recherche par nom ou email.
- **Inscriptions** : formulaire d’inscription, annulation, liste des inscriptions par événement et par participant, statistiques.
- **Tableau de bord** : vue synthétique avec le nombre d’inscriptions et l’occupation des événements.

### Communication avec le backend

Les services Angular utilisent le `HttpClient` pour appeler la gateway sur les routes suivantes :

- `/api/events` → `events-service`
- `/api/participants` → `participants-service`
- `/api/registrations` → `registrations-service`

Cette indirection permet de changer les URLs internes sans impacter le code frontend.

### Captures d’écran

> *Insérer ici les captures d’écran des pages principales :*
> - Page liste des événements.
> - Formulaire d’inscription.
> - Page statistiques d’inscription.

---

## 7. Difficultés rencontrées et solutions apportées

### 7.1 Coexistence de plusieurs microservices et dépendances

**Problème** : le service `registrations-service` dépend des réponses des services `events-service` et `participants-service` pour valider une inscription.

**Solution** : mise en place d’un client HTTP (`app/clients.py`) qui appelle les endpoints de santé et de récupération des ressources. Les appels sont isolés dans des fonctions dédiées et les erreurs sont remontées sous forme de codes HTTP cohérents (`503` si le service est injoignable, `404` si la ressource n’existe pas, `502` en cas d’erreur remontée).

### 7.2 Gestion des places disponibles et des doublons

**Problème** : il faut empêcher l’inscription d’un participant déjà inscrit et refuser l’inscription si l’événement est plein.

**Solution** : vérification explicite avant création :
- appel de `/events/{id}/availability` pour connaître le nombre de places restantes,
- requête en base sur le couple `(event_id, participant_id, status="confirmed")` pour détecter un doublon.

### 7.3 Tests unitaires indépendants d’une base PostgreSQL

**Problème** : lancer PostgreSQL localement pour les tests alourdit la boucle de développement et la CI.

**Solution** : utilisation de **SQLite en mémoire/fichier** dans les tests, en surchargeant la dépendance `get_db` grâce au mécanisme `app.dependency_overrides` de FastAPI. Les appels externes sont simulés avec `monkeypatch`.

### 7.4 Compatibilité du driver PostgreSQL

**Problème** : `psycopg2-binary` nécessite des outils de compilation sous certaines configurations et peut poser problème avec Python 3.14.

**Solution** : remplacement par le driver pure Python **pg8000**, qui n’a besoin d’aucune bibliothèque système native. Le `Dockerfile` est allégé (plus besoin de `gcc` ni de `postgresql-dev`) et la chaîne de build est plus rapide.

---

## 8. Améliorations possibles

### 8.1 Résilience des appels inter-services

Les appels HTTP actuels sont synchrones. En cas de panne temporaire d’un service partenaire, l’inscription échoue immédiatement. On pourrait ajouter :
- un mécanisme de **retry** avec backoff exponentiel,
- un **circuit breaker** pour éviter d’appeler un service en panne,
- une validation asynchrone via une file d’attente (RabbitMQ, Kafka ou Redis Pub/Sub).

### 8.2 Authentification et autorisation

Aujourd’hui, aucun contrôle d’accès n’est implémenté. Une amélioration serait d’ajouter :
- un service d’**authentification** (JWT ou OAuth2),
- des rôles (organisateur, participant, admin),
- une vérification des inscriptions par l’organisateur de l’événement.

### 8.3 Observabilité

- Intégrer des **logs structurés JSON** (déjà prévu via `LOG_LEVEL`).
- Exposer des **métriques Prometheus** pour chaque microservice.
- Ajouter un healthcheck détaillé incluant la base de données et les services dépendants.

### 8.4 Synchronisation des capacités

Le contrôle des places restantes repose actuellement sur une API externe. Pour éviter les conditions de course, on pourrait :
- centraliser la réservation de places dans un **endpoint transactionnel**,
- utiliser un verrou pessimiste ou optimiste côté base de données,
- implémenter une **saga** répartie entre `events-service` et `registrations-service`.

### 8.5 Tests d’intégration

Outre les tests unitaires, il serait utile de mettre en place des **tests de contrat** et des **tests d’intégration** Docker Compose afin de valider le bon fonctionnement de l’ensemble des services démarrés ensemble.
