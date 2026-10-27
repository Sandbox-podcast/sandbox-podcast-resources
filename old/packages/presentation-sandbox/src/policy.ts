/**
 * Politique d'isolation des présentations HTML (master prompt §14.1 et §27.4).
 *
 * Défense en profondeur, trois couches :
 * 1. une origine dédiée, différente de celle de l'application (le serveur applique la politique) ;
 * 2. l'attribut `sandbox` de l'iframe, sans `allow-same-origin` : origine opaque, pas d'accès
 *    aux cookies, au stockage, ni au DOM de l'application ;
 * 3. un en-tête Content-Security-Policy qui coupe tout réseau et toute ressource externe.
 */

export interface SandboxPolicyOptions {
  /**
   * Origines autorisées à afficher la présentation dans une iframe : celle de l'application.
   * Obligatoire. Liste vide : personne, la présentation ne s'affiche dans aucune iframe.
   * `'self'` ne convient pas, l'origine des présentations n'est pas celle de l'application.
   */
  frameAncestors: readonly string[];
  /** Autorise `eval` et `new Function`. Désactivé : une présentation n'en a pas besoin. */
  allowEval?: boolean;
}

/**
 * En-tête Content-Security-Policy servi avec chaque présentation.
 * Seuls les scripts et styles inline, les images, polices et médias en `data:` ou `blob:` passent.
 * Aucun réseau (`connect-src 'none'`), aucune frame, aucun formulaire, aucune base.
 */
export function presentationCsp(options: SandboxPolicyOptions): string {
  const scriptSrc = options.allowEval ? "'unsafe-inline' 'unsafe-eval'" : "'unsafe-inline'";
  return [
    "default-src 'none'",
    `script-src ${scriptSrc}`,
    "style-src 'unsafe-inline'",
    'img-src data: blob:',
    'font-src data:',
    'media-src data: blob:',
    "connect-src 'none'",
    "frame-src 'none'",
    "object-src 'none'",
    "form-action 'none'",
    "base-uri 'none'",
    `frame-ancestors ${options.frameAncestors.length > 0 ? options.frameAncestors.join(' ') : "'none'"}`,
    // Applique aussi le bac à sable quand la page est ouverte directement, hors iframe.
    'sandbox allow-scripts',
  ].join('; ');
}

/** Autres en-têtes de réponse de l'origine des présentations. */
export function presentationHeaders(options: SandboxPolicyOptions): Record<string, string> {
  return {
    'Content-Security-Policy': presentationCsp(options),
    'X-Content-Type-Options': 'nosniff',
    'Referrer-Policy': 'no-referrer',
    'Cross-Origin-Resource-Policy': 'cross-origin',
    'Permissions-Policy':
      'camera=(), microphone=(), geolocation=(), display-capture=(), payment=(), usb=(), clipboard-read=(), clipboard-write=()',
    'Cache-Control': 'no-store',
  };
}

/**
 * Attributs de l'iframe qui affiche une présentation.
 * `sandbox="allow-scripts"` seul : jamais `allow-same-origin`, qui annulerait l'isolation.
 */
export function iframeAttributes(src: string): Record<string, string> {
  return {
    src,
    sandbox: 'allow-scripts',
    referrerpolicy: 'no-referrer',
    allow: '',
    loading: 'eager',
  };
}

/** Vrai si une valeur d'attribut `sandbox` n'annule pas l'isolation. */
export function isSafeSandboxAttribute(value: string): boolean {
  const tokens = value.split(/\s+/).filter((token) => token.length > 0);
  const forbidden = new Set([
    'allow-same-origin',
    'allow-top-navigation',
    'allow-top-navigation-by-user-activation',
    'allow-top-navigation-to-custom-protocols',
    'allow-popups',
    'allow-popups-to-escape-sandbox',
    'allow-forms',
    'allow-modals',
    'allow-downloads',
    'allow-storage-access-by-user-activation',
  ]);
  return tokens.every((token) => !forbidden.has(token));
}
