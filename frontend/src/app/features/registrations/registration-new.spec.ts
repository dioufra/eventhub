import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { provideRouter } from '@angular/router';

import { Configuration as EventsConfig } from '../../core/api/events';
import { Configuration as ParticipantsConfig } from '../../core/api/participants';
import { Configuration as RegistrationsConfig } from '../../core/api/registrations';
import { RegistrationNew } from './registration-new';

/**
 * Régression : le résumé n'apparaissait jamais.
 *
 * selectedEventId et selectedParticipantId étaient de simples propriétés de
 * classe, lues à l'intérieur de computed(). Or un computed ne se recalcule
 * que si un SIGNAL qu'il lit change — une propriété ordinaire n'est pas
 * suivie. selectedEvent() restait donc figé à null, canReview() à false, et
 * le bouton de confirmation n'était jamais rendu.
 *
 * Ces tests vérifient que la sélection déclenche bien le recalcul.
 */
describe('RegistrationNew — réactivité de la sélection', () => {
  let component: RegistrationNew;
  let httpMock: HttpTestingController;

  const EVENT = {
    id: 1,
    title: 'Atelier Docker',
    description: null,
    starts_at: '2026-09-10T14:00:00',
    location: 'Salle B',
    capacity: 10,
    seats_taken: 0,
  };

  const PARTICIPANT = {
    id: 7,
    full_name: 'Frdiouf',
    email: 'frdiouf@gmail.com',
    phone: null,
    type: 'etudiant',
  };

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [RegistrationNew],
      providers: [
        provideHttpClient(),
        provideHttpClientTesting(),
        provideRouter([]),
        // Mêmes providers que app.config.ts : adresse de base vide, donc
        // URL relatives. Sans eux les clients générés retomberaient sur
        // « http://localhost », ce qui casserait le routage par la gateway.
        { provide: EventsConfig, useValue: new EventsConfig({ basePath: '' }) },
        { provide: ParticipantsConfig, useValue: new ParticipantsConfig({ basePath: '' }) },
        { provide: RegistrationsConfig, useValue: new RegistrationsConfig({ basePath: '' }) },
      ],
    });

    component = TestBed.createComponent(RegistrationNew).componentInstance;
    httpMock = TestBed.inject(HttpTestingController);

    // Le composant charge événements et participants dans son constructeur.
    httpMock.expectOne((r) => r.url === '/api/events').flush([EVENT]);
    httpMock.expectOne((r) => r.url === '/api/participants').flush([PARTICIPANT]);
    httpMock
      .expectOne((r) => r.url === `/api/events/${EVENT.id}/availability`)
      .flush({
        event_id: EVENT.id,
        capacity: 10,
        seats_taken: 0,
        seats_available: 10,
        is_full: false,
      });
  });

  afterEach(() => httpMock.verify());

  it('appelle les API en URL relatives', () => {
    // Vérifié implicitement par les expectOne du beforeEach, qui matchent
    // « /api/events » et non « http://localhost/api/events ».
    expect(component.events().length).toBe(1);
    expect(component.participants().length).toBe(1);
  });

  it('ne propose pas de résumé tant que rien n’est sélectionné', () => {
    expect(component.canReview()).toBeFalse();
    expect(component.canConfirm()).toBeFalse();
  });

  it('ne suffit pas de choisir un événement seul', () => {
    component.selectedEventId.set(EVENT.id);
    expect(component.selectedEvent()).toBeTruthy();
    expect(component.canReview()).toBeFalse();
  });

  it('affiche le résumé et autorise la confirmation une fois les deux choix faits', () => {
    component.selectedEventId.set(EVENT.id);
    component.selectedParticipantId.set(PARTICIPANT.id);

    expect(component.selectedEvent()?.title).toBe('Atelier Docker');
    expect(component.selectedParticipant()?.full_name).toBe('Frdiouf');
    expect(component.canReview()).toBeTrue();
    expect(component.canConfirm()).toBeTrue();
    expect(component.seatsLeft()).toBe(10);
  });

  it('filtre les participants au fil de la saisie', () => {
    expect(component.filteredParticipants().length).toBe(1);

    component.participantFilter.set('inconnu');
    expect(component.filteredParticipants().length).toBe(0);

    component.participantFilter.set('frdiouf');
    expect(component.filteredParticipants().length).toBe(1);
  });
});
