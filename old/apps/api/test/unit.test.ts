import { describe, expect, it } from 'vitest';
import {
  hashPassword,
  passwordProblems,
  verifyPassword,
  MAX_PASSWORD_LENGTH,
  MIN_PASSWORD_LENGTH,
} from '../src/auth/password.ts';
import { hashToken, isTokenShape, newToken } from '../src/auth/tokens.ts';
import { loadConfig } from '../src/config.ts';
import { cleanDisplayName, issueRoomToken, roomName } from '../src/livekit.ts';
import { ROLES, can, isRole, type Action, type Role } from '../src/rbac.ts';

const FAST = { N: 2 ** 10, r: 8, p: 1 };

describe('mots de passe', () => {
  it('hache avec un sel propre à chaque appel et vérifie', async () => {
    const [a, b] = [
      await hashPassword('un mot de passe solide', FAST),
      await hashPassword('un mot de passe solide', FAST),
    ];
    expect(a).not.toBe(b);
    expect(a).toMatch(/^scrypt\$1024\$8\$1\$/);
    expect(await verifyPassword('un mot de passe solide', a)).toBe(true);
    expect(await verifyPassword('un mot de passe solidE', a)).toBe(false);
    expect(await verifyPassword('', a)).toBe(false);
  });

  it('normalise Unicode : la même saisie sous deux formes est acceptée', async () => {
    const hash = await hashPassword('café-très-solide', FAST);
    expect(await verifyPassword('café-très-solide', hash)).toBe(true);
  });

  it('refuse sans calcul coûteux un enregistrement malformé ou aux paramètres démesurés', async () => {
    expect(await verifyPassword('x', 'pas-un-hash')).toBe(false);
    expect(await verifyPassword('x', 'bcrypt$10$a$b$c$d')).toBe(false);
    expect(await verifyPassword('x', 'scrypt$0$8$1$AAAA$AAAA')).toBe(false);
    expect(await verifyPassword('x', `scrypt$${String(2 ** 30)}$8$1$AAAA$AAAA`)).toBe(false);
    expect(await verifyPassword('x', 'scrypt$1024$8$99$AAAA$AAAA')).toBe(false);
    expect(await verifyPassword('x', 'scrypt$abc$8$1$AAAA$AAAA')).toBe(false);
  });

  it('applique la politique de mot de passe', () => {
    expect(passwordProblems('x'.repeat(MIN_PASSWORD_LENGTH - 1), 'a@b.fr')).toContain(
      `au moins ${String(MIN_PASSWORD_LENGTH)} caractères`,
    );
    expect(passwordProblems('x'.repeat(MAX_PASSWORD_LENGTH + 1), 'a@b.fr')).toContain(
      `au plus ${String(MAX_PASSWORD_LENGTH)} caractères`,
    );
    expect(passwordProblems('louisette-secret-1', 'louisette@example.org')).toContain(
      "ne doit pas contenir l'adresse e-mail",
    );
    expect(passwordProblems('aaaaaaaaaaaaaa', 'z@y.fr')).toContain(
      'ne doit pas être un seul caractère répété',
    );
    expect(passwordProblems('une phrase de passe correcte', 'z@y.fr')).toEqual([]);
    // Les bornes exactes sont acceptées.
    expect(passwordProblems('ab'.repeat(MIN_PASSWORD_LENGTH / 2), 'z@y.fr')).toEqual([]);
    expect(passwordProblems('ab'.repeat(MAX_PASSWORD_LENGTH / 2), 'z@y.fr')).toEqual([]);
  });
});

describe('jetons', () => {
  it('sont aléatoires, de forme fixe, et seule leur empreinte est comparée', () => {
    const [a, b] = [newToken(), newToken()];
    expect(a).not.toBe(b);
    expect(isTokenShape(a)).toBe(true);
    expect(hashToken(a)).toMatch(/^[0-9a-f]{64}$/);
    expect(hashToken(a)).not.toBe(a);
    expect(hashToken(a)).toBe(hashToken(a));
  });

  it.each([
    undefined,
    null,
    42,
    '',
    'court',
    `${'a'.repeat(43)}!`,
    'a'.repeat(44),
    "'; drop table users; --".padEnd(43, 'a'),
  ])('refuse un jeton de forme invalide : %j', (value) => {
    expect(isTokenShape(value)).toBe(false);
  });
});

describe('droits par rôle (AC-SEC-001, AC-SEC-002)', () => {
  const ACTIONS: Action[] = [
    'podcast:read',
    'podcast:manage-members',
    'episode:read',
    'episode:create',
    'episode:edit-rundown',
    'episode:invite',
    'studio:join',
    'studio:control',
    'recording:control',
  ];
  const EXPECTED: Record<Role, Action[]> = {
    ADMIN: ACTIONS,
    PRODUCER: ACTIONS.filter((a) => a !== 'podcast:manage-members'),
    HOST: ['podcast:read', 'episode:read', 'episode:edit-rundown', 'studio:join'],
    EDITOR: ['podcast:read', 'episode:read', 'episode:edit-rundown'],
    VIEWER: ['podcast:read', 'episode:read'],
  };

  it.each(ROLES)('%s a exactement les droits prévus', (role) => {
    expect(ACTIONS.filter((a) => can(role, a))).toEqual(EXPECTED[role]);
  });

  it('sans rôle, rien n’est permis', () => {
    for (const action of ACTIONS) {
      expect(can(null, action)).toBe(false);
      expect(can(undefined, action)).toBe(false);
    }
  });

  it('reconnaît un rôle valide et rien d’autre (pas d’auto-attribution d’un rôle inventé)', () => {
    expect(isRole('ADMIN')).toBe(true);
    expect(isRole('SUPERADMIN')).toBe(false);
    expect(isRole('admin')).toBe(false);
    expect(isRole(undefined)).toBe(false);
  });
});

describe('configuration', () => {
  it('lit et valide l’environnement', () => {
    const config = loadConfig({
      DATABASE_URL: 'postgres://x',
      ALLOWED_ORIGINS: 'http://a, http://b ,',
      ALLOW_REGISTRATION: 'true',
    });
    expect(config.ALLOWED_ORIGINS).toEqual(['http://a', 'http://b']);
    expect(config.ALLOW_REGISTRATION).toBe(true);
    expect(config.COOKIE_SECURE).toBe(false);
    expect(config.PORT).toBe(3001);
  });

  it('refuse une configuration incohérente', () => {
    expect(() => loadConfig({})).toThrow(/DATABASE_URL/);
    expect(() => loadConfig({ DATABASE_URL: 'x', ALLOW_REGISTRATION: 'oui' })).toThrow(
      /ALLOW_REGISTRATION/,
    );
    expect(() => loadConfig({ DATABASE_URL: 'x', PORT: '99999' })).toThrow(/PORT/);
  });
});

describe('jetons de salle LiveKit', () => {
  const config = loadConfig({
    DATABASE_URL: 'x',
    LIVEKIT_API_KEY: 'cle-de-test',
    LIVEKIT_API_SECRET: 'secret-de-test-assez-long-pour-hs256',
  });
  const episodeId = '11111111-2222-4333-8444-555555555555';
  const participantId = '66666666-7777-4888-9999-000000000000';

  const claims = (jwt: string): Record<string, unknown> =>
    JSON.parse(Buffer.from(jwt.split('.')[1] ?? '', 'base64url').toString('utf8')) as Record<
      string,
      unknown
    >;

  it('fixe l’identité sur l’identifiant de participant et la salle sur l’épisode', async () => {
    const claim = claims(
      await issueRoomToken(config, {
        episodeId,
        participantId,
        displayName: 'Camille',
        role: 'GUEST',
      }),
    );
    expect(claim['sub']).toBe(participantId);
    expect(claim['name']).toBe('Camille');
    expect((claim['video'] as Record<string, unknown>)['room']).toBe(roomName(episodeId));
    expect((claim['video'] as Record<string, unknown>)['roomAdmin']).toBe(false);
    const ttl = Number(claim['exp']) - Number(claim['nbf']);
    expect(ttl).toBeLessThanOrEqual(2 * 3600);
  });

  it('refuse une identité ou une salle qui ne sont pas des UUID (traversée de chemin)', async () => {
    await expect(
      issueRoomToken(config, {
        episodeId,
        participantId: '../../etc/passwd',
        displayName: 'x',
        role: 'GUEST',
      }),
    ).rejects.toThrow(/invalide/);
    await expect(
      issueRoomToken(config, { episodeId: 'ep-1', participantId, displayName: 'x', role: 'GUEST' }),
    ).rejects.toThrow(/invalide/);
  });

  it('refuse sans clés configurées', async () => {
    await expect(
      issueRoomToken(loadConfig({ DATABASE_URL: 'x' }), {
        episodeId,
        participantId,
        displayName: 'x',
        role: 'GUEST',
      }),
    ).rejects.toThrow(/non configuré/);
  });

  it('un invité ne peut pas publier de données, un rôle de régie le peut', async () => {
    const guest = claims(
      await issueRoomToken(config, { episodeId, participantId, displayName: 'G', role: 'GUEST' }),
    );
    const producer = claims(
      await issueRoomToken(config, {
        episodeId,
        participantId,
        displayName: 'P',
        role: 'PRODUCER',
      }),
    );
    expect((guest['video'] as Record<string, unknown>)['canPublishData']).toBe(false);
    expect((producer['video'] as Record<string, unknown>)['canPublishData']).toBe(true);
  });

  it('nettoie un nom affiché : caractères de contrôle retirés, longueur bornée', () => {
    expect(cleanDisplayName('  Ca\u0000mi\u001fl\u007fle  ')).toBe('Camille');
    expect(cleanDisplayName('x'.repeat(500))).toHaveLength(120);
    expect(cleanDisplayName('../../évil')).toBe('../../évil');
  });
});
