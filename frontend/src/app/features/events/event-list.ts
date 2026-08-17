import { Component, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { forkJoin, of } from 'rxjs';
import { catchError, map, switchMap } from 'rxjs/operators';

import { EventsService, EventOut, AvailabilityOut } from '../../core/api/events';

interface EventRow extends EventOut {
  availability?: AvailabilityOut;
}

@Component({
  selector: 'app-event-list',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './event-list.html',
  styleUrl: './event-list.scss',
})
export class EventList {
  // Service généré depuis la spec OpenAPI d'events-service.
  private readonly eventsApi = inject(EventsService);

  readonly events = signal<EventRow[]>([]);
  readonly loading = signal(false);
  readonly error = signal<string | null>(null);

  location = '';
  date = '';

  constructor() {
    this.load();
  }

  load(): void {
    this.loading.set(true);
    this.error.set(null);

    this.eventsApi
      .listEvents(this.date || undefined, this.location || undefined)
      .pipe(
        switchMap((events) => {
          if (!events.length) {
            return of([] as EventRow[]);
          }
          // Pour chaque événement, on demande sa disponibilité.
          return forkJoin(
            events.map((event) =>
              this.eventsApi.availability(event.id).pipe(
                map((availability) => ({ ...event, availability }) as EventRow),
                catchError(() => of(event as EventRow)),
              ),
            ),
          );
        }),
        catchError((err) => {
          this.error.set(
            `Impossible de charger les événements (${err.status ?? 'réseau'})`,
          );
          return of([] as EventRow[]);
        }),
      )
      .subscribe((rows) => {
        this.events.set(rows);
        this.loading.set(false);
      });
  }

  resetFilters(): void {
    this.location = '';
    this.date = '';
    this.load();
  }
}
