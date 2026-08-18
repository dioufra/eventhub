#!/usr/bin/env bash
# =============================================================================
#  EventHub — tests de recette
#
#  Vérifie qu'une pile démarrée répond de bout en bout : disponibilité,
#  validation des entrées, communication inter-services et règles métier.
#
#  Usage :  bash scripts/smoke-test.sh [URL_DE_BASE]
#  Défaut :  http://localhost:8080
# =============================================================================
set -uo pipefail

BASE="${1:-http://localhost:8080}"
PASS=0
FAIL=0

code() { curl -s -o /dev/null -w '%{http_code}' "$@"; }
field() { python3 -c "import sys,json;print(json.load(sys.stdin)$1)" 2>/dev/null; }
post() { curl -s -X POST "$1" -H 'Content-Type: application/json' -d "$2"; }
post_code() { code -X POST "$1" -H 'Content-Type: application/json' -d "$2"; }

check() {
  local label="$1" expected="$2" actual="$3"
  if [ "$expected" = "$actual" ]; then
    printf '  ✅ %-46s %s\n' "$label" "$actual"
    PASS=$((PASS + 1))
  else
    printf '  ❌ %-46s attendu %s, reçu %s\n' "$label" "$expected" "$actual"
    FAIL=$((FAIL + 1))
  fi
}

echo ""
echo "━━━ Tests de recette EventHub ━━━"
echo "    cible : $BASE"
echo ""

echo "1. Disponibilité des services"
check "Gateway"                200 "$(code "$BASE/gateway-health")"
check "Application (frontend)" 200 "$(code "$BASE/")"
check "API Événements"         200 "$(code "$BASE/api/events")"
check "API Participants"       200 "$(code "$BASE/api/participants")"
check "API Inscriptions"       200 "$(code "$BASE/api/registrations")"
check "Statistiques"           200 "$(code "$BASE/api/registrations/stats")"

echo ""
echo "2. Routage côté client (rafraîchissement navigateur)"
check "/events"        200 "$(code "$BASE/events")"
check "/participants"  200 "$(code "$BASE/participants")"
check "/registrations" 200 "$(code "$BASE/registrations")"

echo ""
echo "3. Validation des entrées"
check "Capacité négative refusée" 422 \
  "$(post_code "$BASE/api/events" '{"title":"KO","starts_at":"2026-12-01T10:00:00","location":"X","capacity":-1}')"
check "Titre trop court refusé" 422 \
  "$(post_code "$BASE/api/events" '{"title":"a","starts_at":"2026-12-01T10:00:00","location":"Amphi","capacity":10}')"
check "Email invalide refusé" 422 \
  "$(post_code "$BASE/api/participants" '{"full_name":"Test User","email":"pas-un-email","type":"etudiant"}')"
check "Type de participant invalide refusé" 422 \
  "$(post_code "$BASE/api/participants" '{"full_name":"Test User","email":"t@dit.sn","type":"alien"}')"
check "Événement inexistant" 404 "$(code "$BASE/api/events/999999")"

echo ""
echo "4. Communication entre microservices"
S="$RANDOM$RANDOM"
EVENT_ID=$(post "$BASE/api/events" \
  "{\"title\":\"Recette $S\",\"starts_at\":\"2026-12-01T10:00:00\",\"location\":\"Salle Recette\",\"capacity\":1}" \
  | field "['id']")
P1=$(post "$BASE/api/participants" \
  "{\"full_name\":\"Recette Un\",\"email\":\"r1-$S@dit.sn\",\"type\":\"etudiant\"}" | field "['id']")
P2=$(post "$BASE/api/participants" \
  "{\"full_name\":\"Recette Deux\",\"email\":\"r2-$S@dit.sn\",\"type\":\"externe\"}" | field "['id']")

if [ -z "${EVENT_ID:-}" ] || [ -z "${P1:-}" ]; then
  echo "  ❌ Impossible de créer le jeu de test — arrêt."
  exit 1
fi
echo "     jeu de test : événement=$EVENT_ID (1 place) · participants=$P1,$P2"

check "Email en double refusé" 409 \
  "$(post_code "$BASE/api/participants" "{\"full_name\":\"Doublon\",\"email\":\"r1-$S@dit.sn\",\"type\":\"etudiant\"}")"
check "Inscription valide" 201 \
  "$(post_code "$BASE/api/registrations" "{\"event_id\":$EVENT_ID,\"participant_id\":$P1}")"
check "Participant inexistant refusé" 404 \
  "$(post_code "$BASE/api/registrations" "{\"event_id\":$EVENT_ID,\"participant_id\":999999}")"
check "Événement inexistant refusé" 404 \
  "$(post_code "$BASE/api/registrations" "{\"event_id\":999999,\"participant_id\":$P1}")"

echo ""
echo "5. Règles métier"
check "Place décomptée" "0" \
  "$(curl -s "$BASE/api/events/$EVENT_ID/availability" | field "['seats_available']")"
check "Événement signalé complet" "True" \
  "$(curl -s "$BASE/api/events/$EVENT_ID/availability" | field "['is_full']")"
check "Inscription sur événement complet refusée" 409 \
  "$(post_code "$BASE/api/registrations" "{\"event_id\":$EVENT_ID,\"participant_id\":$P2}")"
check "Double inscription refusée" 409 \
  "$(post_code "$BASE/api/registrations" "{\"event_id\":$EVENT_ID,\"participant_id\":$P1}")"

# La règle « on ne réduit pas la capacité sous le nombre d'inscrits »
# demande un événement à 2 places avec 2 inscrits : sur un événement à
# 1 place, toute capacité inférieure serait déjà rejetée en 422 par la
# validation Pydantic (capacity > 0), avant d'atteindre la règle métier.
EVENT2=$(post "$BASE/api/events" \
  "{\"title\":\"Recette bis $S\",\"starts_at\":\"2026-12-02T10:00:00\",\"location\":\"Salle Bis\",\"capacity\":2}" \
  | field "['id']")
post_code "$BASE/api/registrations" "{\"event_id\":$EVENT2,\"participant_id\":$P1}" >/dev/null
post_code "$BASE/api/registrations" "{\"event_id\":$EVENT2,\"participant_id\":$P2}" >/dev/null
check "Capacité sous le nombre d'inscrits refusée" 409 \
  "$(code -X PUT "$BASE/api/events/$EVENT2" -H 'Content-Type: application/json' -d '{"capacity":1}')"
check "Capacité au-dessus des inscrits acceptée" 200 \
  "$(code -X PUT "$BASE/api/events/$EVENT2" -H 'Content-Type: application/json' -d '{"capacity":5}')"

echo ""
echo "6. Annulation et libération de place"
REG_ID=$(curl -s "$BASE/api/registrations/event/$EVENT_ID" | field "[0]['id']")
check "Annulation" 204 "$(code -X DELETE "$BASE/api/registrations/$REG_ID")"
check "Place rendue disponible" "1" \
  "$(curl -s "$BASE/api/events/$EVENT_ID/availability" | field "['seats_available']")"
check "Réinscription possible" 201 \
  "$(post_code "$BASE/api/registrations" "{\"event_id\":$EVENT_ID,\"participant_id\":$P2}")"

# Nettoyage du jeu de test
curl -s -o /dev/null -X DELETE "$BASE/api/events/$EVENT_ID"
curl -s -o /dev/null -X DELETE "$BASE/api/events/${EVENT2:-0}"
curl -s -o /dev/null -X DELETE "$BASE/api/participants/$P1"
curl -s -o /dev/null -X DELETE "$BASE/api/participants/$P2"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
printf "   Réussis : %s     Échoués : %s\n" "$PASS" "$FAIL"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
[ "$FAIL" -eq 0 ]
