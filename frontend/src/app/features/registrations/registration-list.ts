import { CommonModule } from '@angular/common';
import { Component, inject, signal } from '@angular/core';
import { RouterLink } from '@angular/router';
import { forkJoin, of } from 'rxjs';
import { catchError } from 'rxjs/operators';

import { EventsService } from '../../core/api/events';
import { ParticipantsService } from '../../core/api/participants';
import { RegistrationsService } from '../../core/api/registrations';
import { toUserMessage } from '../../core/utils/http-error';
import { ConfirmDialog } from '../../shared/ui/confirm-dialog';
import { PageHeader } from '../../shared/ui/page-header';
import { StatePanel } from '../../shared/ui/state-panel';

interface Row {
  id: number;
  status: string;
  createdAt?: string;
  participantName: string;
  participantEmail: string;
  eventTitle: string;
  eventDate?: string;
  eventLocation: string;
}

@Component({
  selector: 'app-registration-list',
  standalone: true,
  imports: [CommonModule, RouterLink, PageHeader, StatePanel, ConfirmDialog],
  templateUrl: './registration-list.html',
  styleUrl: './registration-list.scss',
})
export class RegistrationList {
  private readonly registrationsApi = inject(RegistrationsService);
  private readonly eventsApi = inject(EventsService);
  private readonly participantsApi = inject(ParticipantsService);

  readonly rows = signal<Row[]>([]);
  readonly loading = signal(true);
  readonly error = signal<string | null>(null);
  readonly success = signal<string | null>(null);
  readonly pendingCancel = signal<Row | null>(null);
  readonly cancelling = signal(false);

  constructor() {
    this.load();
  }

  load(): void {
    this.loading.set(true);
    this.error.set(null);

    // Les trois services sont indépendants : on rapproche leurs données
    // côté client pour afficher des libellés lisibles plutôt que des ID.
    forkJoin({
      registrations: this.registrationsApi.listRegistrations('confirmed'),
      events: this.eventsApi.listEvents().pipe(catchError(() => of([]))),
      participants: this.participantsApi.listParticipants().pipe(catchError(() => of([]))),
    }).subscribe({
      next: ({ registrations, events, participants }) => {
        const eventById = new Map(events.map((e) => [e.id, e]));
        const participantById = new Map(participants.map((p) => [p.id, p]));

        this.rows.set(
          registrations.map((reg) => {
            const event = eventById.get(reg.event_id);
            const participant = participantById.get(reg.participant_id);
            return {
              id: reg.id,
              status: reg.status,
              createdAt: reg.created_at ?? undefined,
              participantName: participant?.full_name ?? `Participant #${reg.participant_id}`,
              participantEmail: participant?.email ?? '—',
              eventTitle: event?.title ?? `Événement #${reg.event_id}`,
              eventDate: event?.starts_at,
              eventLocation: event?.location ?? '—',
            };
          }),
        );
        this.loading.set(false);
      },
      error: (err) => {
        this.error.set(toUserMessage(err, 'Impossible de charger les inscriptions.'));
        this.loading.set(false);
      },
    });
  }

  confirmCancel(): void {
    const row = this.pendingCancel();
    if (!row) return;

    this.cancelling.set(true);
    this.registrationsApi.cancelRegistration(row.id).subscribe({
      next: () => {
        this.cancelling.set(false);
        this.pendingCancel.set(null);
        this.success.set(`Inscription de ${row.participantName} annulée. La place a été rendue.`);
        setTimeout(() => this.success.set(null), 4500);
        this.load();
      },
      error: (err) => {
        this.cancelling.set(false);
        this.pendingCancel.set(null);
        this.error.set(toUserMessage(err, "L'annulation a échoué."));
      },
    });
  }
}
