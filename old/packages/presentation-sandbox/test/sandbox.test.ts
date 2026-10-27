import { describe, expect, it } from 'vitest';
import {
  MAX_PRESENTATION_BYTES,
  iframeAttributes,
  isSafeSandboxAttribute,
  isTrustedMessage,
  parseSandboxMessage,
  presentationCsp,
  presentationHeaders,
  validatePresentationHtml,
} from '../src/index.ts';

const directives = (csp: string): Map<string, string> =>
  new Map(
    csp.split(';').map((part) => {
      const [name = '', ...rest] = part.trim().split(/\s+/);
      return [name, rest.join(' ')];
    }),
  );

const APP = 'https://app.example';
const options = { frameAncestors: [APP] };

describe('presentationCsp', () => {
  const csp = directives(presentationCsp(options));

  it('coupe tout réseau et toute ressource externe', () => {
    expect(csp.get('default-src')).toBe("'none'");
    expect(csp.get('connect-src')).toBe("'none'");
    expect(csp.get('frame-src')).toBe("'none'");
    expect(csp.get('object-src')).toBe("'none'");
    expect(csp.get('form-action')).toBe("'none'");
    expect(csp.get('base-uri')).toBe("'none'");
  });

  it('ne laisse passer que des scripts et styles inline et des médias en data: ou blob:', () => {
    expect(csp.get('script-src')).toBe("'unsafe-inline'");
    expect(csp.get('style-src')).toBe("'unsafe-inline'");
    expect(csp.get('img-src')).toBe('data: blob:');
    expect(csp.get('font-src')).toBe('data:');
    expect(csp.get('media-src')).toBe('data: blob:');
  });

  it('interdit eval par défaut, et seulement par choix explicite', () => {
    expect(presentationCsp(options)).not.toContain('unsafe-eval');
    expect(presentationCsp({ ...options, allowEval: true })).toContain("'unsafe-eval'");
  });

  it('applique le bac à sable même hors iframe, sans allow-same-origin', () => {
    expect(csp.get('sandbox')).toBe('allow-scripts');
    expect(presentationCsp(options)).not.toContain('allow-same-origin');
  });

  it("n'autorise jamais de source générique, et le réseau seulement pour encadrer la présentation", () => {
    const text = presentationCsp(options);
    expect(text).not.toMatch(/\*/);
    expect(text.replace(/frame-ancestors [^;]*/, '')).not.toMatch(/https?:/);
  });

  it("autorise seulement l'origine de l'application à encadrer la présentation", () => {
    expect(csp.get('frame-ancestors')).toBe(APP);
    expect(directives(presentationCsp({ frameAncestors: [] })).get('frame-ancestors')).toBe(
      "'none'",
    );
    expect(csp.get('frame-ancestors')).not.toContain("'self'");
  });
});

describe('presentationHeaders', () => {
  it('ajoute les en-têtes de durcissement', () => {
    const headers = presentationHeaders(options);
    expect(headers['X-Content-Type-Options']).toBe('nosniff');
    expect(headers['Referrer-Policy']).toBe('no-referrer');
    expect(headers['Permissions-Policy']).toContain('camera=()');
    expect(headers['Permissions-Policy']).toContain('microphone=()');
    expect(headers['Cache-Control']).toBe('no-store');
  });
});

describe('iframeAttributes et sandbox', () => {
  it('produit un sandbox sans allow-same-origin', () => {
    const attributes = iframeAttributes('https://presentations.example/p/1');
    expect(attributes['sandbox']).toBe('allow-scripts');
    expect(isSafeSandboxAttribute(attributes['sandbox'] ?? '')).toBe(true);
    expect(attributes['allow']).toBe('');
    expect(attributes['referrerpolicy']).toBe('no-referrer');
  });

  it.each([
    'allow-scripts allow-same-origin',
    'allow-scripts allow-top-navigation',
    'allow-scripts allow-popups',
    'allow-scripts allow-forms',
    'allow-scripts allow-modals',
    'allow-scripts allow-downloads',
  ])('refuse un sandbox qui annule l’isolation : %s', (value) => {
    expect(isSafeSandboxAttribute(value)).toBe(false);
  });

  it('accepte un sandbox vide ou limité aux scripts', () => {
    expect(isSafeSandboxAttribute('')).toBe(true);
    expect(isSafeSandboxAttribute('allow-scripts')).toBe(true);
  });
});

describe('parseSandboxMessage', () => {
  it('accepte les trois messages autorisés', () => {
    expect(parseSandboxMessage({ type: 'presentation:ready' })).toEqual({
      type: 'presentation:ready',
    });
    expect(parseSandboxMessage({ type: 'presentation:slide', index: 2, total: 10 })).toEqual({
      type: 'presentation:slide',
      index: 2,
      total: 10,
    });
    expect(parseSandboxMessage({ type: 'presentation:resize', height: 720 })).toEqual({
      type: 'presentation:resize',
      height: 720,
    });
  });

  it.each([
    ['type inconnu', { type: 'asset:upload', url: 'http://evil' }],
    ['champ en trop', { type: 'presentation:ready', extra: 1 }],
    ['index non numérique', { type: 'presentation:slide', index: 'x', total: 3 }],
    ['index négatif', { type: 'presentation:slide', index: -1, total: 3 }],
    ['index non entier', { type: 'presentation:slide', index: 1.5, total: 3 }],
    ['hauteur excessive', { type: 'presentation:resize', height: 1e9 }],
    ['chaîne', 'presentation:ready'],
    ['null', null],
    ['tableau', []],
  ])('rejette : %s', (_label, data) => {
    expect(parseSandboxMessage(data)).toBeNull();
  });

  it('ne se laisse pas tromper par un prototype pollué', () => {
    const data = JSON.parse(
      '{"type":"presentation:ready","__proto__":{"polluted":true}}',
    ) as unknown;
    expect(parseSandboxMessage(data)).toBeNull();
  });
});

describe('isTrustedMessage', () => {
  const frame = { id: 'iframe-window' };
  const other = { id: 'autre-fenetre' };

  it("accepte un message de l'iframe en bac à sable (origine « null »)", () => {
    expect(isTrustedMessage({ origin: 'null', source: frame }, frame)).toBe(true);
  });

  it("accepte l'origine dédiée aux présentations quand elle est connue", () => {
    expect(
      isTrustedMessage({ origin: 'https://p.example', source: frame }, frame, 'https://p.example'),
    ).toBe(true);
  });

  it('refuse une autre fenêtre, même avec la bonne origine', () => {
    expect(isTrustedMessage({ origin: 'null', source: other }, frame)).toBe(false);
  });

  it('refuse une origine inattendue', () => {
    expect(
      isTrustedMessage(
        { origin: 'https://evil.example', source: frame },
        frame,
        'https://p.example',
      ),
    ).toBe(false);
  });

  it('refuse une source nulle', () => {
    expect(isTrustedMessage({ origin: 'null', source: null }, null)).toBe(false);
  });
});

describe('validatePresentationHtml', () => {
  const codes = (html: string): string[] => validatePresentationHtml(html).map((i) => i.code);

  it('accepte une présentation autonome', () => {
    const html =
      '<!doctype html><style>body{background:url(data:image/png;base64,AAAA)}</style><h1>Titre</h1><script>document.title="x"</script>';
    expect(validatePresentationHtml(html)).toEqual([]);
  });

  it('signale les ressources externes, dont celles du CSS', () => {
    expect(codes('<img src="https://cdn.example/a.png">')).toContain('EXTERNAL_RESOURCE');
    expect(codes('<script src="//cdn.example/x.js"></script>')).toContain('EXTERNAL_RESOURCE');
    expect(codes('<style>a{background:url(https://x.example/y.png)}</style>')).toContain(
      'EXTERNAL_RESOURCE',
    );
  });

  it('signale les redirections, balises base, frames, formulaires et objets', () => {
    expect(codes('<meta http-equiv="refresh" content="0;url=x">')).toContain('META_REFRESH');
    expect(codes('<base href="/">')).toContain('BASE_TAG');
    expect(codes('<iframe src="x"></iframe>')).toContain('IFRAME');
    expect(codes('<form action="x"></form>')).toContain('FORM');
    expect(codes('<object data="x"></object>')).toContain('OBJECT_EMBED');
  });

  it('signale eval', () => {
    expect(codes('<script>eval("1")</script>')).toContain('EVAL');
    expect(codes('<script>new Function("return 1")</script>')).toContain('EVAL');
  });

  it('signale une présentation trop grosse', () => {
    expect(codes('x'.repeat(MAX_PRESENTATION_BYTES + 1))).toContain('TOO_LARGE');
  });
});
