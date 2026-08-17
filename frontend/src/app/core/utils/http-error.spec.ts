import { HttpErrorResponse } from '@angular/common/http';

import { toUserMessage } from './http-error';

describe('toUserMessage', () => {
  const build = (status: number, error: unknown = null) => new HttpErrorResponse({ status, error });

  it('traduit un serveur injoignable', () => {
    expect(toUserMessage(build(0))).toContain('injoignable');
  });

  it('traduit un 404', () => {
    expect(toUserMessage(build(404))).toContain('introuvable');
  });

  it('traduit un événement complet', () => {
    expect(toUserMessage(build(409, { detail: 'event is full' }))).toBe(
      'Cet événement est complet.',
    );
  });

  it('traduit un email déjà utilisé', () => {
    expect(toUserMessage(build(409, { detail: 'email already used' }))).toContain('déjà utilisée');
  });

  it('traduit une validation 422 champ par champ', () => {
    const err = build(422, { detail: [{ loc: ['body', 'capacity'], msg: 'x' }] });
    expect(toUserMessage(err)).toBe('La capacité est invalide.');
  });

  it("n'expose jamais de message technique brut", () => {
    const message = toUserMessage(build(500, { detail: 'Traceback (most recent call last)' }));
    expect(message).not.toContain('Traceback');
  });

  it('retombe sur le message par défaut hors HttpErrorResponse', () => {
    expect(toUserMessage(new Error('boom'), 'Échec.')).toBe('Échec.');
  });
});
