import { z } from 'zod';

const bool = z
  .enum(['true', 'false'])
  .default('false')
  .transform((v) => v === 'true');

const schema = z.object({
  DATABASE_URL: z.string().min(1),
  /** Origines autorisées pour les requêtes qui modifient l'état avec le cookie de session. */
  ALLOWED_ORIGINS: z
    .string()
    .default('')
    .transform((v) =>
      v
        .split(',')
        .map((o) => o.trim())
        .filter((o) => o.length > 0),
    ),
  ALLOW_REGISTRATION: bool,
  /** `true` hors développement : le cookie n'est envoyé qu'en HTTPS. */
  COOKIE_SECURE: bool,
  SESSION_TTL_HOURS: z.coerce
    .number()
    .int()
    .min(1)
    .max(24 * 30)
    .default(24 * 7),
  LIVEKIT_URL: z.string().default('ws://localhost:7880'),
  LIVEKIT_API_KEY: z.string().default(''),
  LIVEKIT_API_SECRET: z.string().default(''),
  /** Dossier des pages de l'application web (construites par `apps/web`). Absent : l'API ne sert que /api. */
  WEB_DIR: z.string().optional(),
  PORT: z.coerce.number().int().min(0).max(65535).default(3001),
});

export type Config = z.infer<typeof schema>;

/** Lit et valide l'environnement : le serveur ne démarre pas avec une configuration incohérente. */
export function loadConfig(env: Record<string, string | undefined> = process.env): Config {
  const parsed = schema.safeParse(env);
  if (!parsed.success) {
    const problems = parsed.error.issues
      .map((i) => `${i.path.join('.')} : ${i.message}`)
      .join(' ; ');
    throw new Error(`Configuration invalide : ${problems}`);
  }
  return parsed.data;
}
