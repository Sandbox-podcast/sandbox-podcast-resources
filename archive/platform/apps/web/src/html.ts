/**
 * Gabarits HTML sûrs par construction : toute valeur interpolée est échappée, sauf un `SafeHtml` produit par un
 * autre gabarit. Une donnée venant du serveur (titre, nom, notes) ne peut donc jamais devenir du balisage.
 */
export class SafeHtml {
  readonly value: string;

  constructor(value: string) {
    this.value = value;
  }

  toString(): string {
    return this.value;
  }
}

const ESCAPES: Record<string, string> = {
  '&': '&amp;',
  '<': '&lt;',
  '>': '&gt;',
  '"': '&quot;',
  "'": '&#39;',
  '`': '&#96;',
};

export const esc = (value: unknown): string =>
  String(value).replace(/[&<>"'`]/g, (c) => ESCAPES[c] ?? c);

export function html(strings: TemplateStringsArray, ...values: unknown[]): SafeHtml {
  let out = '';
  strings.forEach((chunk, i) => {
    out += chunk;
    if (i >= values.length) return;
    const value = values[i];
    if (value instanceof SafeHtml) out += value.value;
    else if (Array.isArray(value))
      out += value.map((v) => (v instanceof SafeHtml ? v.value : esc(v))).join('');
    else if (value !== null && value !== undefined && value !== false) out += esc(value);
  });
  return new SafeHtml(out);
}

/** Texte déjà sûr (par exemple un littéral du code). Ne jamais l'utiliser avec une donnée externe. */
export const raw = (value: string): SafeHtml => new SafeHtml(value);
