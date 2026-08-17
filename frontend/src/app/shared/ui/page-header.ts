import { Component, input } from '@angular/core';

/** En-tête de page : titre, sous-titre, et CTA projeté à droite. */
@Component({
  selector: 'app-page-header',
  standalone: true,
  template: `
    <header class="page-header">
      <div class="page-header__text">
        <h1>{{ title() }}</h1>
        @if (subtitle()) {
          <p>{{ subtitle() }}</p>
        }
      </div>
      <div class="page-header__actions"><ng-content /></div>
    </header>
  `,
  styles: [
    `
      .page-header {
        display: flex;
        flex-wrap: wrap;
        gap: 1rem;
        align-items: flex-start;
        justify-content: space-between;
        margin-bottom: 1.75rem;
      }
      h1 {
        font-size: 1.6rem;
        color: var(--dit-teal-dark);
      }
      p {
        margin: 0.35rem 0 0;
        color: var(--dit-text-muted);
        font-size: 0.92rem;
        max-width: 62ch;
      }
      .page-header__actions {
        display: flex;
        gap: 0.6rem;
        flex-wrap: wrap;
      }
      @media (max-width: 640px) {
        .page-header__actions {
          width: 100%;
        }
        .page-header__actions ::ng-deep .btn {
          width: 100%;
        }
      }
    `,
  ],
})
export class PageHeader {
  readonly title = input.required<string>();
  readonly subtitle = input<string>('');
}
