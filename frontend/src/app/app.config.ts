import {
  ApplicationConfig,
  provideBrowserGlobalErrorListeners,
  provideZonelessChangeDetection,
} from '@angular/core';
import { provideHttpClient, withFetch } from '@angular/common/http';
import { provideRouter } from '@angular/router';

import { routes } from './app.routes';
import { Configuration as EventsConfig } from './core/api/events';
import { Configuration as ParticipantsConfig } from './core/api/participants';
import { Configuration as RegistrationsConfig } from './core/api/registrations';

/**
 * basePath vide = URL RELATIVES.
 *
 * Les clients générés par openapi-generator utilisent par défaut
 * `basePath = 'http://localhost'`, ce qui casserait tout en conteneur :
 * le navigateur appellerait le port 80 de la machine hôte au lieu de
 * passer par la gateway.
 *
 * Avec une chaîne vide, les appels partent vers `/api/events`, `/api/...` :
 *   · en développement, `proxy.conf.json` les redirige vers 8001/8002/8003
 *   · en conteneur, la gateway Nginx les route vers les microservices
 *
 * La MÊME image fonctionne donc en local, en préproduction et en
 * production, sans variable d'environnement — Angular compilant ses
 * fichiers au build, une variable Docker n'aurait aucun effet.
 */
const RELATIVE_BASE_PATH = '';

export const appConfig: ApplicationConfig = {
  providers: [
    provideBrowserGlobalErrorListeners(),
    provideZonelessChangeDetection(),
    provideRouter(routes),
    provideHttpClient(withFetch()),

    {
      provide: EventsConfig,
      useValue: new EventsConfig({ basePath: RELATIVE_BASE_PATH }),
    },
    {
      provide: ParticipantsConfig,
      useValue: new ParticipantsConfig({ basePath: RELATIVE_BASE_PATH }),
    },
    {
      provide: RegistrationsConfig,
      useValue: new RegistrationsConfig({ basePath: RELATIVE_BASE_PATH }),
    },
  ],
};
