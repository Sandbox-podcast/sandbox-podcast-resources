import { randomBytes, scrypt, timingSafeEqual } from 'node:crypto';

export interface ScryptCost {
  /** Coût CPU/mémoire (puissance de 2). 2¹⁷ est la recommandation OWASP ; les tests utilisent moins. */
  N: number;
  r: number;
  p: number;
}

export const DEFAULT_COST: ScryptCost = { N: 2 ** 17, r: 8, p: 1 };

const KEY_LENGTH = 32;

function derive(password: string, salt: Buffer, cost: ScryptCost): Promise<Buffer> {
  return new Promise((resolve, reject) => {
    scrypt(
      password.normalize('NFKC'),
      salt,
      KEY_LENGTH,
      { N: cost.N, r: cost.r, p: cost.p, maxmem: 256 * 1024 * 1024 },
      (error, key) => {
        if (error) reject(error);
        else resolve(key);
      },
    );
  });
}

/** Format : `scrypt$N$r$p$sel$empreinte` (base64url). Le coût est dans la chaîne : il peut évoluer sans casser les anciens. */
export async function hashPassword(
  password: string,
  cost: ScryptCost = DEFAULT_COST,
): Promise<string> {
  const salt = randomBytes(16);
  const key = await derive(password, salt, cost);
  return `scrypt$${String(cost.N)}$${String(cost.r)}$${String(cost.p)}$${salt.toString('base64url')}$${key.toString('base64url')}`;
}

export async function verifyPassword(password: string, stored: string): Promise<boolean> {
  const parts = stored.split('$');
  if (parts.length !== 6 || parts[0] !== 'scrypt') return false;
  const [, n, r, p, salt, hash] = parts;
  const cost = { N: Number(n), r: Number(r), p: Number(p) };
  if (![cost.N, cost.r, cost.p].every((v) => Number.isInteger(v) && v > 0)) return false;
  // Borne : un enregistrement corrompu ne doit pas permettre de consommer toute la mémoire du serveur.
  if (cost.N > 2 ** 20 || cost.r > 32 || cost.p > 16) return false;
  const expected = Buffer.from(hash ?? '', 'base64url');
  const actual = await derive(password, Buffer.from(salt ?? '', 'base64url'), cost);
  return expected.length === actual.length && timingSafeEqual(expected, actual);
}

export const MIN_PASSWORD_LENGTH = 12;
export const MAX_PASSWORD_LENGTH = 128;

/** Problèmes d'un mot de passe choisi ; liste vide si acceptable. */
export function passwordProblems(password: string, email: string): string[] {
  const problems: string[] = [];
  if (password.length < MIN_PASSWORD_LENGTH)
    problems.push(`au moins ${String(MIN_PASSWORD_LENGTH)} caractères`);
  if (password.length > MAX_PASSWORD_LENGTH)
    problems.push(`au plus ${String(MAX_PASSWORD_LENGTH)} caractères`);
  const local = email.split('@')[0]?.toLowerCase() ?? '';
  if (
    password.toLowerCase() === email.toLowerCase() ||
    (local.length >= 4 && password.toLowerCase().includes(local))
  )
    problems.push("ne doit pas contenir l'adresse e-mail");
  if (/^(.)\1+$/.test(password)) problems.push('ne doit pas être un seul caractère répété');
  return problems;
}
