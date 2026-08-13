# =============================================================================
#  gateway — point d'entrée unique de la plateforme EventHub
# =============================================================================

FROM nginx:1.30.4-alpine

# On remplace la configuration livrée par défaut.
RUN rm /etc/nginx/conf.d/default.conf

COPY nginx.conf        /etc/nginx/conf.d/default.conf
COPY proxy_common.conf /etc/nginx/proxy_common.conf

EXPOSE 80

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD wget --quiet --tries=1 --spider http://127.0.0.1/gateway-health || exit 1

CMD ["nginx", "-g", "daemon off;"]