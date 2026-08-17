import { HttpErrorResponse } from '@angular/common/http';

/**
 * Transforme une erreur HTTP en message lisible par un utilisateur.
 * On n'affiche jamais de trace technique brute dans l'interface.
 */
export function toUserMessage(err: unknown, fallback = "L'opération a échoué."): string {
  if (!(err instanceof HttpErrorResponse)) {
    return fallback;
  }

  switch (err.status) {
    case 0:
      return 'Serveur injoignable. Vérifiez que l’application est démarrée.';
    case 404:
      return 'Élément introuvable. Il a peut-être été supprimé entre-temps.';
    case 409:
      return conflictMessage(err) ?? 'Cette action entre en conflit avec des données existantes.';
    case 422:
      return validationMessage(err) ?? 'Certains champs sont invalides.';
    case 503:
      return 'Un service est temporairement indisponible. Réessayez dans un instant.';
    default:
      return err.status >= 500 ? 'Erreur interne du serveur.' : fallback;
  }
}

function conflictMessage(err: HttpErrorResponse): string | null {
  const detail = typeof err.error?.detail === 'string' ? err.error.detail : '';
  if (detail.includes('full')) return 'Cet événement est complet.';
  if (detail.includes('already registered'))
    return 'Ce participant est déjà inscrit à cet événement.';
  if (detail.includes('email')) return 'Cette adresse email est déjà utilisée.';
  if (detail.includes('capacity'))
    return 'La capacité ne peut pas être inférieure au nombre d’inscrits.';
  return null;
}

/** FastAPI renvoie une 422 détaillée : on la traduit champ par champ. */
function validationMessage(err: HttpErrorResponse): string | null {
  const detail = err.error?.detail;
  if (!Array.isArray(detail) || detail.length === 0) return null;

  const labels: Record<string, string> = {
    title: 'Le titre',
    description: 'La description',
    starts_at: 'La date',
    location: 'Le lieu',
    capacity: 'La capacité',
    full_name: 'Le nom',
    email: "L'email",
    phone: 'Le téléphone',
    type: 'Le type',
  };

  const field = detail[0]?.loc?.at(-1);
  const label = labels[field as string] ?? 'Un champ';
  return `${label} est invalide.`;
}
