import { Routes } from '@angular/router';
import { EventList } from './features/events/event-list';

export const routes: Routes = [
  { path: '', pathMatch: 'full', redirectTo: 'events' },
  { path: 'events', component: EventList, title: 'EventHub — Événements' },
  { path: '**', redirectTo: 'events' },
];
