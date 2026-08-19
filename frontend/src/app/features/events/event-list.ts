import { CommonModule } from '@angular/common';
import { Component, computed, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';
import { forkJoin, of } from 'rxjs';
import { catchError, map, switchMap } from 'rxjs/operators';

import { AvailabilityOut, EventOut, EventsService } from '../../core/api/events';
import { toUserMessage } from '../../core/utils/http-error';
import { ConfirmDialog } from '../../shared/ui/confirm-dialog';
import { PageHeader } from '../../shared/ui/page-header';
import { StatePanel } from '../../shared/ui/state-panel';

interface EventRow extends EventOut {
  availability?: AvailabilityOut;
}

@Component({
  selector: 'app-event-list',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterLink, PageHeader, StatePanel, ConfirmDialog],
  templateUrl: './event-list.html',
  styleUrl: './event-list.scss',
})
export class EventList {
  private readonly api = inject(EventsService);
  private readonly router = inject(Router);

  readonly rows = signal<EventRow[]>([]);
  readonly loading = signal(true);
  readonly error = signal<string | null>(null);
  readonly success = signal<string | null>(null);

  /** Événement en attente de confirmation de suppression. */
  readonly pendingDelete = signal<EventRow | null>(null);
  readonly deleting = signal(false);

  // Lues dans le computed hasFilters : doivent être des signaux.
  readonly location = signal('');
  readonly date = signal('');

  readonly hasFilters = computed(() => !!this.location() || !!this.date());

  constructor() {
    this.load();
  }

  load(): void {
    this.loading.set(true);
    this.error.set(null);

    this.api
      .listEvents(this.date() || undefined, this.location() || undefined)
      .pipe(
        switchMap((events) =>
          events.length
            ? forkJoin(
                events.map((event) =>
                  this.api.availability(event.id).pipe(
                    map((availability) => ({ ...event, availability }) as EventRow),
                    // Un événement dont la disponibilité échoue reste affiché.
                    catchError(() => of(event as EventRow)),
                  ),
                ),
              )
            : of([] as EventRow[]),
        ),
        catchError((err) => {
          this.error.set(toUserMessage(err, 'Impossible de charger les événements.'));
          return of([] as EventRow[]);
        }),
      )
      .subscribe((rows) => {
        this.rows.set(rows);
        this.loading.set(false);
      });
  }

  resetFilters(): void {
    this.location.set('');
    this.date.set('');
    this.load();
  }

  askDelete(row: EventRow): void {
    this.pendingDelete.set(row);
  }

  confirmDelete(): void {
    const row = this.pendingDelete();
    if (!row) return;

    this.deleting.set(true);
    this.api.deleteEvent(row.id).subscribe({
      next: () => {
        this.deleting.set(false);
        this.pendingDelete.set(null);
        this.flash(`L’événement « ${row.title} » a été supprimé.`);
        this.load();
      },
      error: (err) => {
        this.deleting.set(false);
        this.pendingDelete.set(null);
        this.error.set(toUserMessage(err, 'La suppression a échoué.'));
      },
    });
  }

  goToCreate(): void {
    this.router.navigate(['/events/new']);
  }

  private flash(message: string): void {
    this.success.set(message);
    setTimeout(() => this.success.set(null), 4000);
  }
}
