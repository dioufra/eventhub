/** Libellés lisibles des trois types imposés par l'énoncé. */
export function typeLabel(type: string): string {
  return TYPE_LABELS[type] ?? type;
}

export const TYPE_LABELS: Record<string, string> = {
  etudiant: 'Étudiant',
  professeur: 'Professeur',
  externe: 'Externe',
};

export const TYPE_OPTIONS = [
  { value: 'etudiant', label: 'Étudiant', hint: 'Inscrit au DIT' },
  { value: 'professeur', label: 'Professeur', hint: 'Corps enseignant' },
  { value: 'externe', label: 'Externe', hint: 'Invité, partenaire' },
] as const;
