import { CommonModule } from '@angular/common';
import { Component, computed, inject, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';

import { EventsService } from '../../core/api/events';
import { toUserMessage } from '../../core/utils/http-error';
import { PageHeader } from '../../shared/ui/page-header';
import { StatePanel } from '../../shared/ui/state-panel';

@Component({
  selector: 'app-event-form',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, RouterLink, PageHeader, StatePanel],
  templateUrl: './event-form.html',
  styleUrl: './event-form.scss',
})
export class EventForm {
  private readonly fb = inject(FormBuilder);
  private readonly api = inject(EventsService);
  private readonly router = inject(Router);
  private readonly route = inject(ActivatedRoute);

  /** Renseigné en mode édition, null en création. */
  readonly eventId = signal<number | null>(null);
  readonly loading = signal(false);
  readonly saving = signal(false);
  readonly error = signal<string | null>(null);

  readonly isEdit = computed(() => this.eventId() !== null);

  readonly form = this.fb.nonNullable.group({
    title: ['', [Validators.required, Validators.minLength(3), Validators.maxLength(200)]],
    description: [''],
    starts_at: ['', Validators.required],
    location: ['', [Validators.required, Validators.minLength(2), Validators.maxLength(200)]],
    capacity: [50, [Validators.required, Validators.min(1), Validators.max(10000)]],
  });

  constructor() {
    const id = this.route.snapshot.paramMap.get('id');
    if (id) {
      this.eventId.set(Number(id));
      this.loadEvent(Number(id));
    }
  }

  private loadEvent(id: number): void {
    this.loading.set(true);
    this.api.getEvent(id).subscribe({
      next: (event) => {
        this.form.patchValue({
          title: event.title,
          description: event.description ?? '',
          // <input type="datetime-local"> attend « YYYY-MM-DDTHH:mm ».
          starts_at: event.starts_at.slice(0, 16),
          location: event.location,
          capacity: event.capacity,
        });
        this.loading.set(false);
      },
      error: (err) => {
        this.error.set(toUserMessage(err, 'Impossible de charger cet événement.'));
        this.loading.set(false);
      },
    });
  }

  /** Affiche l'erreur d'un champ seulement une fois qu'il a été touché. */
  showError(name: keyof typeof this.form.controls): boolean {
    const control = this.form.controls[name];
    return control.invalid && (control.dirty || control.touched);
  }

  errorFor(name: keyof typeof this.form.controls): string {
    const errors = this.form.controls[name].errors;
    if (!errors) return '';
    if (errors['required']) return 'Ce champ est obligatoire.';
    if (errors['minlength']) return `Au moins ${errors['minlength'].requiredLength} caractères.`;
    if (errors['maxlength']) return `Au plus ${errors['maxlength'].requiredLength} caractères.`;
    if (errors['min']) return 'La capacité doit être d’au moins 1 place.';
    if (errors['max']) return 'La capacité ne peut pas dépasser 10 000 places.';
    return 'Valeur invalide.';
  }

  submit(): void {
    if (this.form.invalid) {
      this.form.markAllAsTouched();
      return;
    }

    this.saving.set(true);
    this.error.set(null);

    const raw = this.form.getRawValue();
    const payload = {
      title: raw.title.trim(),
      description: raw.description.trim() || null,
      // Le backend attend un datetime ISO complet.
      starts_at: new Date(raw.starts_at).toISOString(),
      location: raw.location.trim(),
      capacity: raw.capacity,
    };

    const id = this.eventId();
    const request$ = id ? this.api.updateEvent(id, payload) : this.api.createEvent(payload);

    request$.subscribe({
      next: (event) => {
        this.saving.set(false);
        this.router.navigate(['/events', event.id]);
      },
      error: (err) => {
        this.saving.set(false);
        this.error.set(
          toUserMessage(err, id ? 'La modification a échoué.' : 'La création a échoué.'),
        );
      },
    });
  }
}
