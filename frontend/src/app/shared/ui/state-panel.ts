import { Component, input, output } from '@angular/core';

/**
 * Regroupe les trois états d'une vue de données.
 * Un seul composant plutôt que trois : moins de fichiers, même service rendu.
 */
@Component({
  selector: 'app-state-panel',
  standalone: true,
  template: `
    <div class="state" [class.state--error]="mode() === 'error'">
      @switch (mode()) {
        @case ('loading') {
          <div class="spinner" aria-hidden="true"></div>
          <p class="state__title">{{ title() || 'Chargement…' }}</p>
        }
        @case ('error') {
          <p class="state__title">{{ title() || 'Une erreur est survenue' }}</p>
          <p class="state__msg">{{ message() }}</p>
          @if (retryLabel()) {
            <button type="button" class="btn btn--ghost" (click)="retry.emit()">
              {{ retryLabel() }}
            </button>
          }
        }
        @default {
          <p class="state__title">{{ title() }}</p>
          @if (message()) {
            <p class="state__msg">{{ message() }}</p>
          }
          <ng-content />
        }
      }
    </div>
  `,
  styles: [
    `
      .state {
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 0.6rem;
        padding: 3.5rem 1.5rem;
        text-align: center;
      }
      .state__title {
        margin: 0;
        font-weight: 600;
        color: var(--dit-teal-dark);
      }
      .state__msg {
        margin: 0;
        color: var(--dit-text-muted);
        font-size: 0.9rem;
        max-width: 46ch;
      }
      .state--error .state__title {
        color: var(--dit-danger);
      }
      .spinner {
        width: 26px;
        height: 26px;
        border: 3px solid var(--dit-border);
        border-top-color: var(--dit-teal);
        border-radius: 50%;
        animation: spin 0.7s linear infinite;
      }
      @keyframes spin {
        to {
          transform: rotate(360deg);
        }
      }
    `,
  ],
})
export class StatePanel {
  readonly mode = input.required<'loading' | 'empty' | 'error'>();
  readonly title = input<string>('');
  readonly message = input<string>('');
  readonly retryLabel = input<string>('');
  readonly retry = output<void>();
}
