-- =============================================================================
--  EventHub — création des trois bases logiques
--
--  Exécuté AUTOMATIQUEMENT au tout premier démarrage du conteneur postgres,
--  et UNIQUEMENT si le volume de données est vide.
--
--  Si tu modifies ce fichier après un premier démarrage, il ne sera pas rejoué.
--  Pour le forcer (efface les données) :
--      docker compose down -v && docker compose up -d postgres
--
--  Principe microservices : chaque service possède SA base. Aucun service ne
--  lit les tables d'un autre. Les liens entre services se font par appels REST,
--  jamais par des jointures SQL — c'est pour cela qu'il n'y a aucune clé
--  étrangère entre ces trois bases.
-- =============================================================================

CREATE DATABASE eventhub_events;
CREATE DATABASE eventhub_participants;
CREATE DATABASE eventhub_registrations;

-- L'utilisateur applicatif (POSTGRES_USER) est déjà propriétaire des bases
-- qu'il crée : les tables seront créées au démarrage de chaque service.
