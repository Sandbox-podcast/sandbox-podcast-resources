import type { Actor, Command, StudioPolicy } from './types.ts';

const has = (actor: Actor, ...roles: Actor['roles']): boolean =>
  roles.some((role) => actor.roles.includes(role));

/**
 * Qui peut quoi. Vérifié côté serveur pour toute commande, quel que soit le canal d'entrée.
 * Le frontend n'est jamais une frontière de sécurité.
 */
export function isAllowed(command: Command, policy: StudioPolicy): boolean {
  const { actor } = command;
  switch (command.type) {
    case 'SET_PREVIEW':
    case 'TAKE':
    case 'CUT':
    case 'SHOW_OVERLAY':
    case 'HIDE_OVERLAY':
    case 'SET_SEQUENCE':
      // Le réalisateur automatique peut couper ; l'état « automatique actif » est vérifié ailleurs.
      if (actor.kind === 'AUTO_DIRECTOR') return command.type === 'CUT';
      return has(actor, 'ADMIN', 'PRODUCER') || (policy.hostsMayControl && has(actor, 'HOST'));
    case 'START_RECORDING':
    case 'STOP_RECORDING':
    case 'SET_AUTO_DIRECTOR':
      return actor.kind === 'USER' && has(actor, 'ADMIN', 'PRODUCER');
    case 'REPORT_ASSET':
      return actor.kind === 'SYSTEM';
    case 'GRANT_CONSENT':
      // Seule la personne concernée peut donner son consentement.
      return actor.kind === 'USER' && actor.id === command.participantId;
  }
}
