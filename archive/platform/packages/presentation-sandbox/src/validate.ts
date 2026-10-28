/**
 * Validation statique d'une présentation HTML, avant enregistrement.
 * Elle aide l'auteur (humain ou IA) à corriger tôt. Elle ne remplace pas l'isolation :
 * la sécurité repose sur le bac à sable et la CSP, pas sur cette liste.
 */

export interface PresentationIssue {
  code:
    | 'TOO_LARGE'
    | 'EXTERNAL_RESOURCE'
    | 'META_REFRESH'
    | 'BASE_TAG'
    | 'IFRAME'
    | 'FORM'
    | 'OBJECT_EMBED'
    | 'EVAL';
  message: string;
}

export const MAX_PRESENTATION_BYTES = 2 * 1024 * 1024;

const EXTERNAL_URL = /\b(?:src|href|poster|data)\s*=\s*["']?\s*(?:https?:)?\/\/[^\s"'>]+/gi;
const CSS_URL = /url\(\s*["']?\s*(?:https?:)?\/\/[^)\s"']+/gi;

export function validatePresentationHtml(html: string): PresentationIssue[] {
  const issues: PresentationIssue[] = [];
  const bytes = new TextEncoder().encode(html).length;
  if (bytes > MAX_PRESENTATION_BYTES) {
    issues.push({
      code: 'TOO_LARGE',
      message: `${String(bytes)} octets, maximum ${String(MAX_PRESENTATION_BYTES)}`,
    });
  }
  const external = [...html.matchAll(EXTERNAL_URL), ...html.matchAll(CSS_URL)];
  for (const match of external) {
    issues.push({
      code: 'EXTERNAL_RESOURCE',
      message: `ressource externe bloquée par la CSP : ${match[0].trim().slice(0, 80)}`,
    });
  }
  if (/<meta[^>]+http-equiv\s*=\s*["']?refresh/i.test(html)) {
    issues.push({ code: 'META_REFRESH', message: 'redirection <meta refresh> interdite' });
  }
  if (/<base[\s>]/i.test(html))
    issues.push({ code: 'BASE_TAG', message: 'balise <base> interdite' });
  if (/<iframe[\s>]/i.test(html)) issues.push({ code: 'IFRAME', message: '<iframe> interdite' });
  if (/<form[\s>]/i.test(html)) issues.push({ code: 'FORM', message: '<form> interdit' });
  if (/<(?:object|embed|applet)[\s>]/i.test(html)) {
    issues.push({ code: 'OBJECT_EMBED', message: '<object>, <embed> et <applet> interdits' });
  }
  if (/\beval\s*\(|new\s+Function\s*\(/.test(html)) {
    issues.push({ code: 'EVAL', message: 'eval et new Function sont bloqués par la CSP' });
  }
  return issues;
}
