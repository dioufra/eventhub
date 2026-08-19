# =============================================================================
#  EventHub — raccourcis d'exploitation
#
#  ATTENTION : un Makefile exige des TABULATIONS pour indenter les commandes,
#  jamais des espaces. Sinon : « missing separator. Stop. »
# =============================================================================

COMPOSE       := docker compose
COMPOSE_PROD  := docker compose -f docker-compose.yml -f docker-compose.prod.yml
SERVICES      := events-service participants-service registrations-service
PORT          := $(shell grep -E '^GATEWAY_PORT=' .env 2>/dev/null | cut -d= -f2)
PORT          := $(or $(PORT),8080)

.DEFAULT_GOAL := help
.PHONY: help init up down stop restart build rebuild logs ps sh test test-front \
        smoke db backup clean reset prod prod-down urls

help:  ## Affiche cette aide
	@echo ""
	@echo "  EventHub — commandes disponibles"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) \
		| awk 'BEGIN {FS = ":.*?## "}; {printf "    \033[36m%-12s\033[0m %s\n", $$1, $$2}'
	@echo ""

# ---- Cycle de vie ------------------------------------------------------------

init:  ## Première installation : crée le .env
	@test -f .env || (cp .env.example .env && echo "→ .env créé — renseignez POSTGRES_PASSWORD")
	@echo "→ Prêt. Lancez : make up"

up:  ## Démarre toute la pile en arrière-plan
	$(COMPOSE) up -d
	@$(MAKE) --no-print-directory urls

down:  ## Arrête et supprime les conteneurs (les données sont conservées)
	$(COMPOSE) down

stop:  ## Met la pile en pause sans supprimer les conteneurs
	$(COMPOSE) stop

restart:  ## Redémarre tous les services
	$(COMPOSE) restart

build:  ## Reconstruit les images
	$(COMPOSE) build

rebuild:  ## Reconstruit sans cache puis redémarre
	$(COMPOSE) build --no-cache
	$(COMPOSE) up -d --force-recreate

urls:  ## Affiche les URL du projet
	@echo ""
	@echo "  Application       http://localhost:$(PORT)"
	@echo "  Swagger events    http://localhost:8001/docs"
	@echo "  Swagger particip. http://localhost:8002/docs"
	@echo "  Swagger registr.  http://localhost:8003/docs"
	@echo ""

# ---- Observation -------------------------------------------------------------

logs:  ## Suit les logs (make logs S=events-service pour un seul service)
	$(COMPOSE) logs -f $(S)

ps:  ## État et santé des conteneurs
	$(COMPOSE) ps

sh:  ## Ouvre un shell dans un conteneur (make sh S=events-service)
	$(COMPOSE) exec $(or $(S),events-service) sh

# ---- Qualité -----------------------------------------------------------------

test:  ## Tests unitaires des 3 microservices
	@for s in $(SERVICES); do \
		echo "─── $$s ───"; \
		(cd $$s && python3 -m pytest -q) || exit 1; \
	done
	@echo "✅ Tests backend passés"

test-front:  ## Tests unitaires du frontend Angular
	@cd frontend && npm test -- --watch=false --browsers=ChromeHeadless

smoke:  ## Tests de recette sur la pile démarrée
	@bash scripts/smoke-test.sh http://localhost:$(PORT)

# ---- Base de données ---------------------------------------------------------

db:  ## Session psql (make db D=eventhub_events)
	$(COMPOSE) exec postgres psql -U $${POSTGRES_USER:-eventhub} -d $(or $(D),postgres)

backup:  ## Sauvegarde les 3 bases dans backup-<date>.sql
	@$(COMPOSE) exec -T postgres pg_dumpall -U $${POSTGRES_USER:-eventhub} \
		> backup-$$(date +%F-%H%M).sql
	@echo "→ Sauvegarde créée"

# ---- Nettoyage ---------------------------------------------------------------

clean:  ## Supprime conteneurs et images du projet (données conservées)
	$(COMPOSE) down --rmi local

reset:  ## ⚠️ SUPPRIME TOUT, Y COMPRIS LA BASE DE DONNÉES
	@echo "⚠️  Cette action détruit les données de la base."
	@read -r -p "Confirmer ? [y/N] " ok && [ "$$ok" = "y" ]
	$(COMPOSE) down -v --rmi local
	@echo "→ Projet réinitialisé"

# ---- Production --------------------------------------------------------------

prod:  ## Démarre depuis les images publiées sur le registre
	$(COMPOSE_PROD) pull
	$(COMPOSE_PROD) up -d

prod-down:  ## Arrête la pile de production
	$(COMPOSE_PROD) down
