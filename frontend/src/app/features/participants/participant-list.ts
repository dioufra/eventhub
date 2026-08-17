import { CommonModule } from '@angular/common';
import { Component, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { RouterLink } from '@angular/router';

import { ParticipantOut, ParticipantsService } from '../../core/api/participants';
import { toUserMessage } from '../../core/utils/http-error';
import { ConfirmDialog } from '../../shared/ui/confirm-dialog';
import { PageHeader } from '../../shared/ui/page-header';
import { StatePanel } from '../../shared/ui/state-panel';
import { typeLabel } from './participant-types';

@Component({
  selector: 'app-participant-list',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterLink, PageHeader, StatePanel, ConfirmDialog],
  templateUrl: './participant-list.html',
  styleUrl: './participant-list.scss',
})
export class ParticipantList {
  private readonly api = inject(ParticipantsService);

  readonly rows = signal<ParticipantOut[]>([]);
  readonly loading = signal(true);
  readonly error = signal<string | null>(null);
  readonly success = signal<string | null>(null);
  readonly pendingDelete = signal<ParticipantOut | null>(null);
  readonly deleting = signal(false);

  readonly typeLabel = typeLabel;
  search = '';

  constructor() {
    this.load();
  }

  load(): void {
    this.loading.set(true);
    this.error.set(null);
    this.api.listParticipants(this.search || undefined).subscribe({
      next: (rows) => {
        this.rows.set(rows);
        this.loading.set(false);
      },
      error: (err) => {
        this.error.set(toUserMessage(err, 'Impossible de charger les participants.'));
        this.loading.set(false);
      },
    });
  }

  resetSearch(): void {
    this.search = '';
    this.load();
  }

  confirmDelete(): void {
    const row = this.pendingDelete();
    if (!row) return;

    this.deleting.set(true);
    this.api.deleteParticipant(row.id).subscribe({
      next: () => {
        this.deleting.set(false);
        this.pendingDelete.set(null);
        this.success.set(`${row.full_name} a été supprimé.`);
        setTimeout(() => this.success.set(null), 4000);
        this.load();
      },
      error: (err) => {
        this.deleting.set(false);
        this.pendingDelete.set(null);
        this.error.set(toUserMessage(err, 'La suppression a échoué.'));
      },
    });
  }
}
