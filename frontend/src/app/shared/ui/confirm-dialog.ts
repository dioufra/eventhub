import { Component, input, output } from '@angular/core';

/** Boîte de confirmation modale pour les actions destructrices. */
@Component({
  selector: 'app-confirm-dialog',
  standalone: true,
  template: `
    <div class="backdrop" (click)="cancel.emit()">
      <div
        class="dialog card"
        role="dialog"
        aria-modal="true"
        [attr.aria-label]="title()"
        (click)="$event.stopPropagation()"
      >
        <div class="card__body">
          <h3>{{ title() }}</h3>
          <p>{{ message() }}</p>
          <div class="dialog__actions">
            <button
              type="button"
              class="btn btn--ghost"
              (click)="cancel.emit()"
              [disabled]="busy()"
            >
              Annuler
            </button>
            <button
              type="button"
              class="btn btn--danger"
              (click)="confirm.emit()"
              [disabled]="busy()"
            >
              {{ busy() ? 'En cours…' : confirmLabel() }}
            </button>
          </div>
        </div>
      </div>
    </div>
  `,
  styles: [
    `
      .backdrop {
        position: fixed;
        inset: 0;
        background: rgba(4, 50, 58, 0.45);
        display: grid;
        place-items: center;
        padding: 1rem;
        z-index: 60;
      }
      .dialog {
        max-width: 420px;
        width: 100%;
        box-shadow: var(--shadow-lg);
      }
      h3 {
        font-size: 1.05rem;
        color: var(--dit-teal-dark);
      }
      p {
        margin: 0.5rem 0 1.4rem;
        color: var(--dit-text-muted);
        font-size: 0.92rem;
      }
      .dialog__actions {
        display: flex;
        gap: 0.6rem;
        justify-content: flex-end;
      }
    `,
  ],
})
export class ConfirmDialog {
  readonly title = input<string>('Confirmer');
  readonly message = input<string>('');
  readonly confirmLabel = input<string>('Confirmer');
  readonly busy = input<boolean>(false);
  readonly confirm = output<void>();
  readonly cancel = output<void>();
}
