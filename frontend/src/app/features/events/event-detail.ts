import { CommonModule } from '@angular/common';
import { Component, inject, signal } from '@angular/core';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { forkJoin, of } from 'rxjs';
import { catchError } from 'rxjs/operators';

import { AvailabilityOut, EventOut, EventsService } from '../../core/api/events';
import { ParticipantsService } from '../../core/api/participants';
import { RegistrationsService } from '../../core/api/registrations';
import { toUserMessage } from '../../core/utils/http-error';
import { PageHeader } from '../../shared/ui/page-header';
import { StatePanel } from '../../shared/ui/state-panel';

interface Attendee {
  registrationId: number;
  name: string;
  email: string;
  type: string;
}

@Component({
  selector: 'app-event-detail',
  standalone: true,
  imports: [CommonModule, RouterLink, PageHeader, StatePanel],
  templateUrl: './event-detail.html',
  styleUrl: './event-detail.scss',
})
export class EventDetail {
  private readonly route = inject(ActivatedRoute);
  private readonly eventsApi = inject(EventsService);
  private readonly participantsApi = inject(ParticipantsService);
  private readonly registrationsApi = inject(RegistrationsService);

  readonly event = signal<EventOut | null>(null);
  readonly availability = signal<AvailabilityOut | null>(null);
  readonly attendees = signal<Attendee[]>([]);
  readonly loading = signal(true);
  readonly error = signal<string | null>(null);

  constructor() {
    this.load(Number(this.route.snapshot.paramMap.get('id')));
  }

  private load(id: number): void {
    this.loading.set(true);
    forkJoin({
      event: this.eventsApi.getEvent(id),
      availability: this.eventsApi.availability(id).pipe(catchError(() => of(null))),
      registrations: this.registrationsApi.listByEvent(id).pipe(catchError(() => of([]))),
      participants: this.participantsApi.listParticipants().pipe(catchError(() => of([]))),
    }).subscribe({
      next: ({ event, availability, registrations, participants }) => {
        this.event.set(event);
        this.availability.set(availability);

        // Le service inscriptions ne stocke que des identifiants : on les
        // rapproche des participants pour afficher des noms lisibles.
        const byId = new Map(participants.map((p) => [p.id, p]));
        this.attendees.set(
          registrations.map((reg) => {
            const p = byId.get(reg.participant_id);
            return {
              registrationId: reg.id,
              name: p?.full_name ?? `Participant #${reg.participant_id}`,
              email: p?.email ?? '—',
              type: p?.type ?? '—',
            };
          }),
        );
        this.loading.set(false);
      },
      error: (err) => {
        this.error.set(toUserMessage(err, 'Impossible de charger cet événement.'));
        this.loading.set(false);
      },
    });
  }
}
