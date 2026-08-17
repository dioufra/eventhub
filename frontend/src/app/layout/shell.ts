import { Component, signal } from '@angular/core';
import { RouterLink, RouterLinkActive, RouterOutlet } from '@angular/router';

interface NavItem {
  path: string;
  label: string;
  icon: string;
}

/** Coquille applicative : sidebar de navigation + zone de contenu. */
@Component({
  selector: 'app-shell',
  standalone: true,
  imports: [RouterLink, RouterLinkActive, RouterOutlet],
  templateUrl: './shell.html',
  styleUrl: './shell.scss',
})
export class Shell {
  /** Ouverture du tiroir de navigation sur mobile. */
  readonly menuOpen = signal(false);

  readonly nav: NavItem[] = [
    { path: '/events', label: 'Événements', icon: 'calendar' },
    { path: '/participants', label: 'Participants', icon: 'users' },
    { path: '/registrations', label: 'Inscriptions', icon: 'ticket' },
  ];

  toggleMenu(): void {
    this.menuOpen.update((open) => !open);
  }

  closeMenu(): void {
    this.menuOpen.set(false);
  }
}
