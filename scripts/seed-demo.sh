#!/usr/bin/env bash
# =============================================================================
#  EventHub — jeu de données de démonstration
#
#  Crée six événements, douze participants et une quarantaine d'inscriptions,
#  choisis pour illustrer tous les cas d'usage : événement complet, capacités
#  variées, les trois types de participant, et une annulation.
#
#  Usage :  bash scripts/seed-demo.sh [URL_DE_BASE]
#  Défaut :  http://localhost:8080
#
#  ⚠️ Le script VIDE les trois bases avant de les remplir.
# =============================================================================
set -uo pipefail

BASE="${1:-http://localhost:8080}"

if ! curl -sf "$BASE/gateway-health" >/dev/null 2>&1; then
  echo "❌ Application injoignable sur $BASE"
  echo "   Démarrez-la avec « make up », puis vérifiez GATEWAY_PORT dans .env"
  exit 1
fi

python3 - "$BASE" <<'PY'
import json, sys, urllib.error, urllib.request

BASE = sys.argv[1]


def call(method, path, payload=None):
    data = json.dumps(payload).encode() if payload else None
    req = urllib.request.Request(f"{BASE}{path}", data=data, method=method,
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req) as r:
            body = r.read()
            return r.status, (json.loads(body) if body else None)
    except urllib.error.HTTPError as e:
        return e.code, None


# ---------------------------------------------------------------- purge -----
for path in ("/api/registrations", "/api/events", "/api/participants"):
    _, rows = call("GET", path)
    for row in rows or []:
        call("DELETE", f"{path}/{row['id']}")
print("  base vidée")

# --------------------------------------------------------------- events -----
EVENTS = [
    ("Conférence — L'IA au service de l'Afrique",
     "Table ronde avec des chercheurs et entrepreneurs du continent sur les "
     "usages concrets de l'intelligence artificielle.",
     "2026-09-15T09:00:00", "Amphithéâtre A", 120),
    ("Atelier Docker & Conteneurisation",
     "Atelier pratique : construire, orchestrer et déployer une application "
     "conteneurisée.",
     "2026-09-18T14:00:00", "Salle Informatique B", 25),
    ("Séminaire — Cybersécurité et protection des données",
     "Panorama des menaces actuelles et des bonnes pratiques de protection.",
     "2026-09-22T10:00:00", "Amphithéâtre B", 80),
    # Capacité volontairement basse : cet événement sera complet, ce qui
    # permet de démontrer le refus d'inscription et l'affichage « Complet ».
    ("Masterclass — Machine Learning appliqué",
     "De la préparation des données au déploiement d'un modèle en production.",
     "2026-09-25T09:30:00", "Laboratoire IA", 4),
    ("Journée portes ouvertes du DIT",
     "Présentation des filières, rencontres avec les enseignants et visite "
     "des laboratoires.",
     "2026-10-03T08:30:00", "Campus principal", 300),
    ("Hackathon FinTech Dakar",
     "48 heures pour concevoir une solution financière innovante.",
     "2026-10-10T08:00:00", "Espace Coworking", 60),
]

events = []
for title, desc, when, loc, cap in EVENTS:
    st, ev = call("POST", "/api/events", {
        "title": title, "description": desc,
        "starts_at": when, "location": loc, "capacity": cap})
    if st == 201:
        events.append(ev)
print(f"  {len(events)} événements")

# --------------------------------------------------------- participants -----
PARTICIPANTS = [
    ("Aïcha Ndiaye",        "aicha.ndiaye@dit.sn",        "+221 77 512 44 08", "etudiant"),
    ("Mamadou Ba",          "mamadou.ba@dit.sn",          "+221 76 330 19 72", "etudiant"),
    ("Fatou Sarr",          "fatou.sarr@dit.sn",          "+221 78 604 55 21", "etudiant"),
    ("Ousmane Diallo",      "ousmane.diallo@dit.sn",      "+221 77 218 90 34", "etudiant"),
    ("Awa Camara",          "awa.camara@dit.sn",          "+221 70 145 62 87", "etudiant"),
    ("Ibrahima Fall",       "ibrahima.fall@dit.sn",       "+221 77 903 27 16", "etudiant"),
    ("Pr. Cheikh Diop",     "cheikh.diop@dit.sn",         "+221 33 869 44 10", "professeur"),
    ("Dr. Mariama Sy",      "mariama.sy@dit.sn",          "+221 33 869 44 12", "professeur"),
    ("Pr. Abdoulaye Gueye", "abdoulaye.gueye@dit.sn",     "+221 33 869 44 15", "professeur"),
    ("Sokhna Mbaye",        "s.mbaye@sonatel.sn",         "+221 77 441 08 93", "externe"),
    # Sans téléphone : montre le rendu d'une valeur absente dans la liste.
    ("Moussa Traoré",       "m.traore@orange-digital.sn", None,                "externe"),
    ("Khadija Diouf",       "k.diouf@wave.com",           "+221 76 552 71 40", "externe"),
]

participants = []
for name, email, phone, typ in PARTICIPANTS:
    st, p = call("POST", "/api/participants", {
        "full_name": name, "email": email, "phone": phone, "type": typ})
    if st == 201:
        participants.append(p)
print(f"  {len(participants)} participants")

# --------------------------------------------------------- inscriptions -----
P = [p["id"] for p in participants]
E = [e["id"] for e in events]

REPARTITION = [
    (E[0], P[:8]),    # Conférence
    (E[1], P[:6]),    # Atelier Docker
    (E[2], P[3:9]),   # Séminaire
    (E[3], P[:4]),    # Masterclass → COMPLET
    (E[4], P),        # Portes ouvertes
    (E[5], P[6:]),    # Hackathon
]

total = 0
for event_id, pids in REPARTITION:
    for pid in pids:
        st, _ = call("POST", "/api/registrations",
                     {"event_id": event_id, "participant_id": pid})
        if st == 201:
            total += 1
print(f"  {total} inscriptions")

# Une annulation, pour que l'historique ne soit pas uniforme et que la
# libération de place soit visible.
_, regs = call("GET", f"/api/registrations/event/{E[5]}")
if regs:
    call("DELETE", f"/api/registrations/{regs[0]['id']}")
    print("  1 annulation (place rendue)")

# ------------------------------------------------------------ résumé --------
print("\n  Événement                                    Places")
print("  " + "-" * 54)
for e in events:
    _, av = call("GET", f"/api/events/{e['id']}/availability")
    etat = "COMPLET" if av["is_full"] else f"{av['seats_available']}/{av['capacity']}"
    print(f"  {e['title'][:44]:44} {etat:>8}")
PY

echo ""
echo "✅ Jeu de démonstration en place — $BASE"
