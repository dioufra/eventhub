import { CommonModule } from '@angular/common';
import { Component, computed, inject, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';

import { ParticipantsService } from '../../core/api/participants';
import { toUserMessage } from '../../core/utils/http-error';
import { PageHeader } from '../../shared/ui/page-header';
import { StatePanel } from '../../shared/ui/state-panel';
import { TYPE_OPTIONS } from './participant-types';

@Component({
  selector: 'app-participant-form',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, RouterLink, PageHeader, StatePanel],
  templateUrl: './participant-form.html',
  styleUrl: './participant-form.scss',
})
export class ParticipantForm {
  private readonly fb = inject(FormBuilder);
  private readonly api = inject(ParticipantsService);
  private readonly router = inject(Router);
  private readonly route = inject(ActivatedRoute);

  readonly typeOptions = TYPE_OPTIONS;
  readonly participantId = signal<number | null>(null);
  readonly loading = signal(false);
  readonly saving = signal(false);
  readonly error = signal<string | null>(null);
  readonly isEdit = computed(() => this.participantId() !== null);

  readonly form = this.fb.nonNullable.group({
    full_name: ['', [Validators.required, Validators.minLength(2), Validators.maxLength(150)]],
    email: ['', [Validators.required, Validators.email, Validators.maxLength(150)]],
    phone: ['', Validators.maxLength(30)],
    type: ['etudiant', Validators.required],
  });

  constructor() {
    const id = this.route.snapshot.paramMap.get('id');
    if (id) {
      this.participantId.set(Number(id));
      this.load(Number(id));
    }
  }

  private load(id: number): void {
    this.loading.set(true);
    this.api.getParticipant(id).subscribe({
      next: (p) => {
        this.form.patchValue({
          full_name: p.full_name,
          email: p.email,
          phone: p.phone ?? '',
          type: p.type,
        });
        this.loading.set(false);
      },
      error: (err) => {
        this.error.set(toUserMessage(err, 'Impossible de charger ce participant.'));
        this.loading.set(false);
      },
    });
  }

  showError(name: keyof typeof this.form.controls): boolean {
    const c = this.form.controls[name];
    return c.invalid && (c.dirty || c.touched);
  }

  errorFor(name: keyof typeof this.form.controls): string {
    const errors = this.form.controls[name].errors;
    if (!errors) return '';
    if (errors['required']) return 'Ce champ est obligatoire.';
    if (errors['email']) return 'Adresse email invalide.';
    if (errors['minlength']) return `Au moins ${errors['minlength'].requiredLength} caractères.`;
    if (errors['maxlength']) return `Au plus ${errors['maxlength'].requiredLength} caractères.`;
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
      full_name: raw.full_name.trim(),
      email: raw.email.trim(),
      phone: raw.phone.trim() || null,
      type: raw.type as 'etudiant' | 'professeur' | 'externe',
    };

    const id = this.participantId();
    const request$ = id
      ? this.api.updateParticipant(id, payload)
      : this.api.createParticipant(payload);

    request$.subscribe({
      next: () => {
        this.saving.set(false);
        this.router.navigate(['/participants']);
      },
      error: (err) => {
        this.saving.set(false);
        this.error.set(toUserMessage(err, id ? 'La modification a échoué.' : "L'ajout a échoué."));
      },
    });
  }
}
