import { CommonModule } from '@angular/common';
import { Component, computed, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';
import { forkJoin, of } from 'rxjs';
import { catchError, map } from 'rxjs/operators';

import { AvailabilityOut, EventOut, EventsService } from '../../core/api/events';
import { ParticipantOut, ParticipantsService } from '../../core/api/participants';
import { RegistrationsService } from '../../core/api/registrations';
import { toUserMessage } from '../../core/utils/http-error';
import { PageHeader } from '../../shared/ui/page-header';
import { StatePanel } from '../../shared/ui/state-panel';
import { typeLabel } from '../participants/participant-types';

interface EventChoice extends EventOut {
  availability?: AvailabilityOut;
}

/**
 * Parcours d'inscription en trois étapes :
 * événement → participant → résumé et confirmation.
 */
@Component({
  selector: 'app-registration-new',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterLink, PageHeader, StatePanel],
  templateUrl: './registration-new.html',
  styleUrl: './registration-new.scss',
})
export class RegistrationNew {
  private readonly eventsApi = inject(EventsService);
  private readonly participantsApi = inject(ParticipantsService);
  private readonly registrationsApi = inject(RegistrationsService);
  private readonly router = inject(Router);

  readonly events = signal<EventChoice[]>([]);
  readonly participants = signal<ParticipantOut[]>([]);
  readonly loading = signal(true);
  readonly submitting = signal(false);
  readonly error = signal<string | null>(null);
  readonly loadError = signal<string | null>(null);

  readonly typeLabel = typeLabel;

  // Ces trois valeurs sont lues à l'intérieur de computed() ci-dessous.
  // Elles DOIVENT être des signaux : un computed ne se recalcule que si un
  // signal qu'il lit change. Avec de simples propriétés, selectedEvent()
  // restait figé à null et le résumé n'apparaissait jamais.
  readonly selectedEventId = signal<number | null>(null);
  readonly selectedParticipantId = signal<number | null>(null);
  readonly participantFilter = signal('');

  readonly selectedEvent = computed(
    () => this.events().find((e) => e.id === this.selectedEventId()) ?? null,
  );

  readonly selectedParticipant = computed(
    () => this.participants().find((p) => p.id === this.selectedParticipantId()) ?? null,
  );

  readonly isFull = computed(() => this.selectedEvent()?.availability?.is_full === true);

  readonly seatsLeft = computed(() => this.selectedEvent()?.availability?.seats_available ?? null);

  /** Le résumé n'apparaît qu'une fois les deux sélections faites. */
  readonly canReview = computed(() => !!this.selectedEvent() && !!this.selectedParticipant());

  readonly canConfirm = computed(() => this.canReview() && !this.isFull() && !this.submitting());

  readonly filteredParticipants = computed(() => {
    const needle = this.participantFilter().trim().toLowerCase();
    if (!needle) return this.participants();
    return this.participants().filter(
      (p) => p.full_name.toLowerCase().includes(needle) || p.email.toLowerCase().includes(needle),
    );
  });

  constructor() {
    this.load();
  }

  load(): void {
    this.loading.set(true);
    this.loadError.set(null);

    forkJoin({
      events: this.eventsApi.listEvents(),
      participants: this.participantsApi.listParticipants(),
    })
      .pipe(
        // On enrichit chaque événement de sa disponibilité pour pouvoir
        // afficher les places restantes dès le sélecteur.
        map(({ events, participants }) => ({ events, participants })),
      )
      .subscribe({
        next: ({ events, participants }) => {
          this.participants.set(participants);

          if (!events.length) {
            this.events.set([]);
            this.loading.set(false);
            return;
          }

          forkJoin(
            events.map((event) =>
              this.eventsApi.availability(event.id).pipe(
                map((availability) => ({ ...event, availability }) as EventChoice),
                catchError(() => of(event as EventChoice)),
              ),
            ),
          ).subscribe((enriched) => {
            this.events.set(enriched);
            this.loading.set(false);
          });
        },
        error: (err) => {
          this.loadError.set(toUserMessage(err, 'Impossible de charger les données.'));
          this.loading.set(false);
        },
      });
  }

  submit(): void {
    const event = this.selectedEvent();
    const participant = this.selectedParticipant();
    if (!event || !participant || this.isFull()) return;

    this.submitting.set(true);
    this.error.set(null);

    this.registrationsApi
      .createRegistration({ event_id: event.id, participant_id: participant.id })
      .subscribe({
        next: () => {
          this.submitting.set(false);
          this.router.navigate(['/registrations']);
        },
        error: (err) => {
          this.submitting.set(false);
          this.error.set(toUserMessage(err, "L'inscription a échoué."));
          // La disponibilité a pu changer entre-temps : on la rafraîchit.
          this.load();
        },
      });
  }
}
