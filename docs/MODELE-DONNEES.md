# Modèle de données

Deux vues sont nécessaires pour décrire fidèlement EventHub. Le modèle
conceptuel décrit **le domaine métier** ; le modèle physique décrit
**la répartition réelle** imposée par l'architecture microservices.

Présenter la première sans la seconde laisserait croire à l'existence de clés
étrangères entre les trois tables — ce qui n'est pas le cas.

---

## 1. Modèle conceptuel (MCD)

Vue métier, indépendante de la répartition physique.

```
   ┌──────────────────────────┐            ┌──────────────────────────┐
   │        Evenement         │            │        Participant       │
   ├──────────────────────────┤            ├──────────────────────────┤
   │ id            INT        │            │ id            INT        │
   │ title         VARCHAR200 │            │ full_name     VARCHAR150 │
   │ description   TEXT       │            │ email         VARCHAR150 │
   │ starts_at     DATETIME   │            │ phone         VARCHAR30  │
   │ location      VARCHAR200 │            │ type          VARCHAR20  │
   │ capacity      INT        │            └──────────────────────────┘
   │ seats_taken   INT        │                         │
   └──────────────────────────┘                         │
                │ 1,n                                   │ 1,n
                │                                       │
          ╭─────┴─────╮                          ╭──────┴──────╮
          │  concerne │                          │ s'inscrire  │
          ╰─────┬─────╯                          ╰──────┬──────╯
                │ 1,1                                   │ 1,1
                │        ┌──────────────────────┐       │
                └────────┤     Inscription      ├───────┘
                         ├──────────────────────┤
                         │ id       INT         │
                         │ status   VARCHAR20   │
                         └──────────────────────┘

   Contrainte : un participant ne peut être inscrit qu'une seule fois
                à un même événement — unicité du couple porté par
                les deux associations.
```

### Choix de modélisation

**`Inscription` est une entité associative**, et non une simple association.
Elle porte son propre identifiant, son propre statut (`confirmed` /
`cancelled`) et son propre cycle de vie : une inscription annulée reste en
base pour l'historique et les statistiques. Une association Merise classique
n'aurait pas permis de la référencer ni de l'annuler individuellement.

**`seats_taken` appartient à `Evenement`**, et non à `Inscription`. C'est un
compteur dénormalisé, détenu par le service Événements. Il évite de compter
les inscriptions à chaque consultation — ce qui, dans une architecture
distribuée, exigerait un appel réseau — et il permet de réserver une place de
façon atomique, sous verrou, avant même que l'inscription n'existe.

**`status` plutôt qu'une suppression physique.** L'annulation est logique :
elle préserve l'historique et permet de distinguer « jamais inscrit » de
« inscrit puis annulé ».

---

## 2. Modèle physique (MLD)

Vue réelle. Chaque entité réside dans **sa propre base de données**,
conformément au principe microservices : un service ne lit jamais les tables
d'un autre.

```
  ┌─ eventhub_events ─────────┐  ┌─ eventhub_participants ───┐  ┌─ eventhub_registrations ──────┐
  │ events                    │  │ participants              │  │ registrations                 │
  ├───────────────────────────┤  ├───────────────────────────┤  ├───────────────────────────────┤
  │ id            PK          │  │ id            PK          │  │ id                PK          │
  │ title         NOT NULL    │  │ full_name     NOT NULL    │  │ event_id          NOT NULL ○  │
  │ description               │  │ email         UNIQUE      │  │ participant_id    NOT NULL ○  │
  │ starts_at     NOT NULL ▸  │  │ phone                     │  │ status            NOT NULL    │
  │ location      NOT NULL ▸  │  │ type          NOT NULL    │  │ created_at, updated_at        │
  │ capacity      NOT NULL    │  │ created_at, updated_at    │  │                               │
  │ seats_taken   NOT NULL    │  │                           │  │ UNIQUE (event_id,             │
  │ created_at, updated_at    │  │                           │  │         participant_id)       │
  │                           │  │                           │  │                               │
  │ CHECK capacity > 0        │  │                           │  │                               │
  │ CHECK seats_taken >= 0    │  │                           │  │                               │
  │ CHECK seats_taken         │  │                           │  │                               │
  │       <= capacity         │  │                           │  │                               │
  └───────────▲───────────────┘  └───────────▲───────────────┘  └───────┬───────────────┬───────┘
              │                              │                          │               │
              │  POST /api/events/{id}/      │  GET /api/participants/  │               │
              │       seats/reserve          │      {id}                │               │
              └──────────────────────────────┴──────────────────────────┘───────────────┘
                          appels REST — AUCUNE clé étrangère

     ▸ colonne indexée        ○ référence LOGIQUE, validée par appel REST
```

### Ce que la séparation implique

**Aucune clé étrangère entre les trois tables.** Elle serait techniquement
impossible : PostgreSQL ne peut pas contraindre une colonne vers une table
d'une autre base. `event_id` et `participant_id` sont des références
*logiques*, validées au moment de l'inscription par appel REST.

**Aucune jointure SQL possible entre services.** Afficher « le nom du
participant inscrit à tel événement » demande trois appels, agrégés par le
frontend — et non un `JOIN`.

**Aucune suppression en cascade.** Supprimer un événement laisse ses
inscriptions orphelines. Le contrôle est fait en amont, côté interface, qui
refuse la suppression d'un événement ayant des inscriptions. Une solution
complète passerait par un bus de messages (voir « Améliorations possibles »).

**L'intégrité repose sur deux mécanismes complémentaires** : les contraintes
locales à chaque base — unicité de l'email, unicité du couple inscription,
`CHECK` sur les capacités — et la validation applicative par appels REST pour
tout ce qui traverse une frontière de service.

---

## 3. Correspondance entre les deux vues

| Concept métier | Traduction physique |
|---|---|
| Association `concerne` | Colonne `event_id`, validée par REST |
| Association `s'inscrire` | Colonne `participant_id`, validée par REST |
| Unicité de l'inscription | `UNIQUE (event_id, participant_id)` |
| Cardinalité `1,n` côté Evenement | Aucune contrainte SQL — garantie applicative |
| Places restantes | `capacity - seats_taken`, calculé par le service Événements |

C'est précisément l'écart entre ces deux colonnes qui caractérise une
architecture microservices : **ce qu'une base unique garantirait par
contrainte, un système distribué doit le garantir par protocole.**
