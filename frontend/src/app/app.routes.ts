import { Routes } from '@angular/router';

import { Shell } from './layout/shell';

export const routes: Routes = [
  {
    path: '',
    component: Shell,
    children: [
      { path: '', pathMatch: 'full', redirectTo: 'events' },

      {
        path: 'events',
        title: 'Événements — EventHub',
        loadComponent: () => import('./features/events/event-list').then((m) => m.EventList),
      },
      {
        path: 'events/new',
        title: 'Créer un événement — EventHub',
        loadComponent: () => import('./features/events/event-form').then((m) => m.EventForm),
      },
      {
        path: 'events/:id',
        title: 'Détail de l’événement — EventHub',
        loadComponent: () => import('./features/events/event-detail').then((m) => m.EventDetail),
      },
      {
        path: 'events/:id/edit',
        title: 'Modifier l’événement — EventHub',
        loadComponent: () => import('./features/events/event-form').then((m) => m.EventForm),
      },

      {
        path: 'participants',
        title: 'Participants — EventHub',
        loadComponent: () =>
          import('./features/participants/participant-list').then((m) => m.ParticipantList),
      },
      {
        path: 'participants/new',
        title: 'Ajouter un participant — EventHub',
        loadComponent: () =>
          import('./features/participants/participant-form').then((m) => m.ParticipantForm),
      },
      {
        path: 'participants/:id/edit',
        title: 'Modifier le participant — EventHub',
        loadComponent: () =>
          import('./features/participants/participant-form').then((m) => m.ParticipantForm),
      },

      {
        path: 'registrations',
        title: 'Inscriptions — EventHub',
        loadComponent: () =>
          import('./features/registrations/registration-list').then((m) => m.RegistrationList),
      },
      {
        path: 'registrations/new',
        title: 'Nouvelle inscription — EventHub',
        loadComponent: () =>
          import('./features/registrations/registration-new').then((m) => m.RegistrationNew),
      },

      { path: '**', redirectTo: 'events' },
    ],
  },
];
