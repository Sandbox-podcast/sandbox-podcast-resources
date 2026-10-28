import { chromium, type Browser } from 'playwright-core';
import { afterAll, beforeAll, describe, expect, it } from 'vitest';
import { startHarness, type Harness, type Mode } from '../src/harness.ts';

interface AttackResult {
  name: string;
  outcome: 'BLOCKED' | 'SUCCEEDED';
  detail: string;
}

interface Run {
  harness: Harness;
  results: AttackResult[];
  parentUrl: string;
  pwned: string | null;
  xss: boolean;
  cookie: string;
  accepted: unknown[];
  rejected: number;
  ticksDuring: number;
  raw: { origin: string; type: string }[];
}

interface ProbeWindow {
  probe: {
    report: unknown;
    ticks: number;
    xss: boolean;
    accepted: unknown[];
    rejected: number;
    raw: { origin: string; data: { type?: string } | null }[];
  };
}

// Chrome est lancé à la collecte : `it.skipIf` est évalué avant les `beforeAll`.
let browser: Browser | undefined;
try {
  browser = await chromium.launch({ channel: 'chrome', headless: true });
} catch {
  browser = undefined;
}
const chromeAvailable = browser !== undefined;

afterAll(async () => {
  await browser?.close();
});

async function run(mode: Mode): Promise<Run> {
  if (!browser) throw new Error('Chrome indisponible');
  const harness = await startHarness(mode);
  const page = await browser.newPage();
  try {
    await page.goto(harness.appUrl);
    await page.waitForFunction(
      () => (window as unknown as ProbeWindow).probe.report !== undefined,
      undefined,
      {
        timeout: 25_000,
      },
    );
    const results = await page.evaluate(
      () => (window as unknown as ProbeWindow).probe.report as AttackResult[],
    );
    // En mode sécurisé, la présentation bloque ensuite son propre processeur : l'application doit rester réactive.
    const before = await page.evaluate(() => (window as unknown as ProbeWindow).probe.ticks);
    await page.waitForTimeout(1500);
    const after = await page.evaluate(() => (window as unknown as ProbeWindow).probe.ticks);
    const state = await page.evaluate(() => {
      const probe = (window as unknown as ProbeWindow).probe;
      return {
        parentUrl: location.href,
        pwned: document.body.getAttribute('data-pwned'),
        xss: probe.xss,
        cookie: document.cookie,
        accepted: probe.accepted,
        rejected: probe.rejected,
        raw: probe.raw.map((r) => ({ origin: r.origin, type: r.data?.type ?? '?' })),
      };
    });
    return { harness, results, ticksDuring: after - before, ...state };
  } finally {
    await page.close();
  }
}

const outcome = (results: readonly AttackResult[], name: string): AttackResult | undefined =>
  results.find((r) => r.name === name);

// « cadre imbriqué vers l'application » n'est pas dans cette liste : Chrome déclenche `onload` même pour
// un cadre bloqué (page d'erreur). La preuve est côté serveur : aucune requête `/framed` ne doit arriver.
const BLOCKED_ATTACKS = [
  "lire le DOM de l'application",
  "lire les cookies de l'application",
  "lire le localStorage de l'application",
  'lire ses propres cookies',
  'lire son propre localStorage',
  "modifier le DOM de l'application",
  "fetch vers l'application avec cookies",
  'fetch vers un site externe',
  'balise image vers un site externe',
  'script externe injecté',
  'WebSocket vers un site externe',
  'ouvrir une fenêtre',
  'accéder à la caméra',
  'enregistrer un service worker',
  'eval',
  'new Function',
];

describe('présentation malveillante dans le bac à sable (AC-HTML-005, AC-HTML-006, AC-SEC-003)', () => {
  let secure: Run | undefined;

  beforeAll(async () => {
    if (chromeAvailable) secure = await run('secure');
  }, 60_000);

  afterAll(async () => {
    await secure?.harness.close();
  });

  it.skipIf(!chromeAvailable)(
    'la présentation s’exécute et peut parler à l’application (contrôle positif)',
    () => {
      expect(outcome(secure?.results ?? [], 'script inline exécuté')?.outcome).toBe('SUCCEEDED');
      expect(secure?.raw.some((r) => r.type === 'presentation:ready')).toBe(true);
    },
  );

  it.skipIf(!chromeAvailable).each(BLOCKED_ATTACKS)('bloque : %s', (name) => {
    const result = outcome(secure?.results ?? [], name);
    expect(result, `attaque « ${name} » non exécutée`).toBeDefined();
    expect(result?.outcome, `${name} : ${result?.detail ?? ''}`).toBe('BLOCKED');
  });

  it.skipIf(!chromeAvailable)(
    'aucune requête n’atteint le serveur « attaquant » ni les routes de l’application',
    () => {
      expect(secure?.harness.hits.evil).toEqual([]);
      expect(secure?.harness.hits.evilUpgrades).toEqual([]);
      expect(secure?.harness.hits.app).toEqual([]);
    },
  );

  it.skipIf(!chromeAvailable)(
    'ne navigue pas la fenêtre principale et ne modifie pas l’application',
    () => {
      expect(secure?.parentUrl).toBe(`${secure?.harness.appUrl ?? ''}/`);
      expect(secure?.pwned).toBeNull();
      expect(secure?.cookie).toContain('session=APP_SECRET_COOKIE');
    },
  );

  it.skipIf(!chromeAvailable)('la présentation vit dans une origine opaque', () => {
    expect(outcome(secure?.results ?? [], 'document.origin')?.detail).toBe('null');
  });

  it.skipIf(!chromeAvailable)('n’accepte que les messages autorisés et bien formés', () => {
    expect(secure?.accepted).toEqual([
      { type: 'presentation:ready' },
      { type: 'presentation:slide', index: 0, total: 3 },
    ]);
    expect(secure?.rejected).toBeGreaterThanOrEqual(2);
  });

  it.skipIf(!chromeAvailable)(
    'un titre contenant du HTML ne s’exécute pas dans l’application',
    () => {
      expect(secure?.xss).toBe(false);
    },
  );

  it.skipIf(!chromeAvailable)(
    'une boucle infinie dans la présentation ne gèle pas l’application',
    () => {
      // 1,5 s à un relevé toutes les 100 ms : une application gelée n'en ferait aucun.
      expect(secure?.ticksDuring).toBeGreaterThanOrEqual(10);
    },
  );
});

describe('contrôle négatif : le banc détecte une configuration dangereuse', () => {
  let vulnerable: Run | undefined;

  beforeAll(async () => {
    if (chromeAvailable) vulnerable = await run('vulnerable');
  }, 60_000);

  afterAll(async () => {
    await vulnerable?.harness.close();
  });

  it.skipIf(!chromeAvailable)(
    'avec allow-same-origin, sans CSP et sur l’origine de l’application, les attaques réussissent',
    () => {
      const succeeded = (vulnerable?.results ?? []).filter(
        (r) => BLOCKED_ATTACKS.includes(r.name) && r.outcome === 'SUCCEEDED',
      );
      expect(succeeded.length).toBeGreaterThanOrEqual(8);
      expect(
        outcome(vulnerable?.results ?? [], "lire les cookies de l'application")?.detail,
      ).toContain('APP_SECRET_COOKIE');
      expect(vulnerable?.pwned).toBe('1');
      expect(vulnerable?.harness.hits.app).toContain('/api/secret');
      expect(vulnerable?.harness.hits.evil.length).toBeGreaterThan(0);
    },
  );
});

describe('présentation ouverte directement, hors iframe', () => {
  it.skipIf(!chromeAvailable)(
    'la directive CSP « sandbox » isole aussi la page ouverte seule',
    async () => {
      if (!browser) throw new Error('Chrome indisponible');
      const harness = await startHarness('secure');
      const page = await browser.newPage();
      try {
        await page.goto(`${harness.sandboxUrl}/p/direct`);
        const state = await page.evaluate(() => {
          const w = window as unknown as { __o?: string; __cookie?: string; __ls?: string };
          return { origin: w.__o, cookie: w.__cookie, storage: w.__ls };
        });
        expect(state).toEqual({
          origin: 'null',
          cookie: 'SecurityError',
          storage: 'SecurityError',
        });
      } finally {
        await page.close();
        await harness.close();
      }
    },
    30_000,
  );
});
