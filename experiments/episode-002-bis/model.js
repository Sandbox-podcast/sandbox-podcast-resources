import { videoMedia } from './media.js';
import { useCases } from './visuals.js';
export const chapters = [
  {
    id: 'radar',
    label: 'LE RADAR',
    color: '#47d7f4',
    image: 'radar-hero.png',
    cue: 'Les signaux de la semaine',
    start: 0,
  },
  {
    id: 'build',
    label: 'LE BUILD',
    color: '#91e5bc',
    image: 'build-hero.png',
    cue: 'Les outils, les usages, la méthode',
    start: 11,
  },
  {
    id: 'clash',
    label: 'LE CLASH',
    color: '#ff725e',
    image: 'clash-hero.png',
    cue: 'Quatre questions. Trois points de vue.',
    start: 16,
  },
  {
    id: 'beta',
    label: 'LA BÊTA',
    color: '#f1c77d',
    image: 'beta-hero.png',
    cue: 'Vos prochains essais',
    start: 21,
  },
];

// originalNumber renvoie au contenu conservé, jamais à un fichier partagé.
export const scenes = [
  { id: 'radar', chapter: 'radar', kind: 'opener', title: 'Le Radar', originalNumber: 1 },
  {
    id: 'muse',
    chapter: 'radar',
    kind: 'orbit',
    title: 'Muse Wonder',
    headline: 'Un agent qui va au bout.',
    originalNumber: 2,
    mark: 'META',
    figure: '1 M',
    unit: 'tokens de contexte annoncés',
    caution: 'Capacités annoncées par Meta. Accès distinct pour Muse Wonder Full.',
  },
  {
    id: 'gemini',
    chapter: 'radar',
    kind: 'context',
    title: 'Gemini 4 Argon',
    headline: 'La guerre des modèles continue.',
    originalNumber: 3,
    mark: 'GOOGLE',
    figure: '1 M',
    unit: 'tokens de contexte annoncés',
    caution: 'Performances annoncées par Google. Accès selon les offres.',
  },
  {
    id: 'replication',
    chapter: 'radar',
    kind: 'network',
    title: "L'IA se réplique ?",
    headline: 'Et si elle passait de machine en machine ?',
    originalNumber: 4,
    mark: 'ANTHROPIC',
    figure: '8 / 9',
    unit: "appareils testés compatibles avec l'inférence",
    caution: 'Évaluation en laboratoire. Pas de ver IA observé en circulation.',
  },
  {
    id: 'claude',
    chapter: 'radar',
    kind: 'terminal',
    title: 'Claude contourne les limites',
    headline: 'Finir la tâche. À quel prix ?',
    originalNumber: 5,
    mark: 'ANTHROPIC',
    figure: '4',
    unit: 'familles de contournements décrites',
    caution: 'Cas rapportés par Anthropic, avec un impact observé limité.',
  },
  {
    id: 'maia',
    chapter: 'radar',
    kind: 'chip',
    title: 'Maia 300',
    headline: 'Microsoft dessine sa propre puce.',
    originalNumber: 6,
    mark: 'MICROSOFT',
    figure: '2027',
    unit: 'déploiement annoncé pour Maia 300',
    caution: 'Feuille de route Microsoft. Aucun abandon de Nvidia annoncé.',
  },
  {
    id: 'glasses',
    chapter: 'radar',
    kind: 'glasses',
    title: 'Lunettes IA',
    headline: 'Qui sait que vous filmez ?',
    originalNumber: 7,
    mark: 'VIE PRIVÉE',
    figure: 'EN DÉBAT',
    unit: 'restriction ciblée proposée en Norvège',
    caution: 'Proposition temporaire dans certains lieux, pas une interdiction adoptée.',
  },
  {
    id: 'rea',
    chapter: 'radar',
    kind: 'reverse',
    title: 'REA',
    headline: 'Refaire une fonction. Et après ?',
    originalNumber: 8,
    mark: 'OPEN SOURCE',
    figure: 'MIT',
    unit: 'licence du dépôt REA',
    caution: 'ArtCraft suit une démarche clean-room indépendante de REA.',
  },
  {
    id: 'runway',
    chapter: 'radar',
    kind: 'film',
    title: 'Claude devient-il Spielberg ?',
    headline: 'Un agent derrière la caméra.',
    originalNumber: 9,
    mark: 'RUNWAY',
    figure: 'API + MCP',
    unit: "deux voies d'accès distinctes",
    caution: 'Les clips se génèrent. La direction et le montage restent à construire.',
  },
  {
    id: 'cold',
    chapter: 'radar',
    kind: 'fridge',
    title: 'La chaîne du froid piratée',
    headline: 'Quand le logiciel fait chauffer les frigos.',
    originalNumber: 10,
    mark: 'CYBERATTAQUE',
    figure: '50 °C',
    unit: 'température rapportée dans une chambre froide',
    caution: 'Chiffre rapporté par la presse. Pertes totales et attribution incertaines.',
  },
  {
    id: 'persuasion',
    chapter: 'radar',
    kind: 'conversation',
    title: "L'IA peut-elle vous convaincre ?",
    headline: 'Une conversation qui change les convictions.',
    originalNumber: 11,
    mark: 'PERSUASION',
    figure: '~20 %',
    unit: 'baisse moyenne de conviction rapportée',
    caution: 'Étude sous examen éditorial. Test Reddit préliminaire et non autorisé.',
  },
  { id: 'build', chapter: 'build', kind: 'opener', title: 'Le Build', originalNumber: 12 },
  {
    id: 'artisans',
    chapter: 'build',
    kind: 'shop',
    title: "L'IA dans votre commerce",
    originalNumber: 13,
  },
  {
    id: 'usages',
    chapter: 'build',
    kind: 'uses',
    title: "Où l'IA vous aide",
    originalNumber: 14,
  },
  {
    id: 'tools',
    chapter: 'build',
    kind: 'tools',
    title: 'Du besoin à votre application',
    originalNumber: 15,
  },
  {
    id: 'method',
    chapter: 'build',
    kind: 'method',
    title: 'Décrire, montrer, puis tester',
    originalNumber: 16,
  },
  { id: 'clash', chapter: 'clash', kind: 'opener', title: 'Le Clash', originalNumber: 18 },
  {
    id: 'tickets',
    chapter: 'clash',
    kind: 'debate',
    title: 'Lire les tickets ?',
    originalNumber: 19,
  },
  {
    id: 'legacy',
    chapter: 'clash',
    kind: 'debate',
    title: 'Sauver le legacy ?',
    originalNumber: 20,
  },
  {
    id: 'review',
    chapter: 'clash',
    kind: 'debate',
    title: 'Relire le code IA ?',
    originalNumber: 21,
  },
  {
    id: 'dev',
    chapter: 'clash',
    kind: 'debate',
    title: 'Savoir coder demain ?',
    originalNumber: 22,
  },
  { id: 'beta', chapter: 'beta', kind: 'opener', title: 'La Bêta', originalNumber: null },
  {
    id: 'comments',
    chapter: 'beta',
    kind: 'comments',
    title: 'À vous de jouer',
    originalNumber: 17,
  },
];

export function stepCount(scene, episode) {
  if (scene.chapter === 'radar') return 1;
  if (['opener', 'debate', 'shop', 'comments', 'demo'].includes(scene.kind)) return 1;
  if (scene.kind === 'method') return 3;
  if (scene.kind === 'uses') return useCases.length;
  return Math.max(
    1,
    episode.original.slides.find((s) => s.n === scene.originalNumber)?.items.length ?? 1,
  );
}

export function initialState() {
  return {
    scene: 0,
    step: 0,
    frozen: false,
    blackout: false,
    media: '',
    view: 'visual',
    positions: {},
    speaker: '',
    timerUntil: 0,
  };
}

export function normalizeState(input, episode) {
  const value = input && typeof input === 'object' ? input : {};
  const scene = Number.isInteger(value.scene)
    ? Math.max(0, Math.min(scenes.length - 1, value.scene))
    : 0;
  const step = Number.isInteger(value.step)
    ? Math.max(0, Math.min(stepCount(scenes[scene], episode) - 1, value.step))
    : 0;
  const positions = {};
  for (const topic of scenes.filter((s) => s.kind === 'debate')) {
    positions[topic.id] = {};
    for (const host of ['Lou', 'Loïc', 'Nico']) {
      const position = value.positions?.[topic.id]?.[host];
      positions[topic.id][host] = ['Oui', 'Non', 'Ça dépend'].includes(position) ? position : '';
    }
  }
  return {
    scene,
    step,
    frozen: value.frozen === true,
    blackout: value.blackout === true,
    media: videoMedia[value.media]?.scene === scenes[scene].id ? value.media : '',
    view: ['visual', 'fact', 'zoom'].includes(value.view) ? value.view : 'visual',
    positions,
    speaker: ['Lou', 'Loïc', 'Nico'].includes(value.speaker) ? value.speaker : '',
    timerUntil: Number.isFinite(value.timerUntil) ? Math.max(0, value.timerUntil) : 0,
  };
}

export function transition(state, action, episode) {
  const next = { ...state };
  if (action.type === 'scene') {
    next.scene = action.index;
    next.step = 0;
    next.media = '';
    next.view = 'visual';
    next.speaker = '';
    next.timerUntil = 0;
  }
  if (action.type === 'step') next.step += action.delta;
  if (action.type === 'toggle' && ['frozen', 'blackout'].includes(action.key))
    next[action.key] = !next[action.key];
  if (action.type === 'view') next.view = action.view;
  if (action.type === 'speaker') next.speaker = action.host;
  if (action.type === 'timer') next.timerUntil = action.until;
  if (action.type === 'media') next.media = action.id;
  if (action.type === 'position' && scenes[state.scene].kind === 'debate') {
    const id = scenes[state.scene].id;
    next.positions = {
      ...state.positions,
      [id]: { ...state.positions[id], [action.host]: action.value },
    };
  }
  return normalizeState(next, episode);
}

export function indexFromHash(hash) {
  const id = hash.replace(/^#/, '');
  const named = scenes.findIndex((scene) => scene.id === id);
  if (named >= 0) return named;
  const match = /^(?:slide-)?(\d+)$/.exec(id);
  return match ? Math.max(0, Math.min(scenes.length - 1, Number(match[1]) - 1)) : 0;
}

// Un parcours unique : chaque point, puis le sujet suivant. Le retour est symétrique.
export function navigationActions(state, direction, episode) {
  const count = stepCount(scenes[state.scene], episode);
  if (direction > 0) {
    if (state.step < count - 1) return [{ type: 'step', delta: 1 }];
    return state.scene < scenes.length - 1 ? [{ type: 'scene', index: state.scene + 1 }] : [];
  }
  if (state.step > 0) return [{ type: 'step', delta: -1 }];
  if (state.scene === 0) return [];
  const previous = state.scene - 1;
  return [
    { type: 'scene', index: previous },
    { type: 'step', delta: stepCount(scenes[previous], episode) - 1 },
  ];
}
