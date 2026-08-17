# =============================================================================
#  frontend — build Angular puis service statique par Nginx
#
#  Build multi-étapes : l'étape 1 a besoin de Node et de node_modules
#  (~500 Mo) ; l'image finale ne contient que des fichiers statiques (~55 Mo).
# =============================================================================

# -----------------------------------------------------------------------------
# ÉTAPE 1 — build : compile l'application avec le CLI Angular
# -----------------------------------------------------------------------------
FROM node:20-alpine AS build

WORKDIR /app

# Le compilateur Angular est gourmand : sans cette limite relevée, le build
# peut échouer sur « JavaScript heap out of memory », notamment en CI.
ENV NODE_OPTIONS=--max-old-space-size=4096

# package*.json seuls d'abord : couche mise en cache, réinstallée uniquement
# si les dépendances changent. Sur Angular cette étape dure ~60 s.
COPY package.json package-lock.json ./

# npm ci (et non npm install) installe EXACTEMENT le contenu du lock :
# c'est la condition d'un build reproductible.
RUN npm ci --legacy-peer-deps

COPY . .

RUN npm run build -- --configuration=production

# -----------------------------------------------------------------------------
# ÉTAPE 2 — runtime : Nginx sert les fichiers statiques
# -----------------------------------------------------------------------------
FROM nginx:1.30.4-alpine

RUN rm /etc/nginx/conf.d/default.conf
COPY nginx.conf /etc/nginx/conf.d/default.conf

# ⚠️ CHEMIN CRITIQUE. Angular 17+ (builder @angular/build:application) produit
# un sous-dossier « browser ». Se tromper ici donne un build réussi, un
# conteneur « healthy »… et une page blanche, sans aucun message d'erreur.
# Pour vérifier :  npm run build && find dist -name index.html
COPY --from=build /app/dist/frontend/browser /usr/share/nginx/html

EXPOSE 80

# Indispensable : la gateway attend « condition: service_healthy ».
# wget est fourni par busybox dans l'image Alpine.
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD wget --quiet --tries=1 --spider http://127.0.0.1/health || exit 1

# daemon off : Nginx doit rester au premier plan, sinon Docker considère
# que le processus principal est terminé et arrête le conteneur.
CMD ["nginx", "-g", "daemon off;"]
