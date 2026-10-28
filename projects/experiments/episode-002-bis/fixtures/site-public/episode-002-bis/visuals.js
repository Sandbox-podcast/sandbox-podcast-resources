import { sourceMedia } from './media.js';
export const escapeText = (value = '') =>
  String(value).replace(
    /[&<>"']/g,
    (character) =>
      ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[character],
  );
const e = escapeText;
export const useCases = [
  {
    sector: 'Commerçant',
    title: 'Fidélité et relances par SMS',
    action:
      'Une base de données clients, avec une interface pour saisir leurs achats et créditer leurs points de fidélité. Un système intelligent envoie vos promotions par SMS aux clients qui ne sont pas passés en magasin depuis X mois.',
    gain: 'Faire revenir les clients absents avec vos promotions.',
    note: "Créer une base de données clients avec une interface pour saisir les achats et créditer les points de fidélité. Le système de relance cible les clients qui ne sont pas passés en magasin depuis X mois et leur envoie les promotions par SMS. Le délai d'inactivité se règle en mois. Prévoir l'accord aux SMS, la désinscription et une validation avant envoi. Mesurer les retours et la marge après remise et coût SMS.",
  },
  {
    sector: 'Agence immobilière',
    title: 'Explorer le bien, poser ses questions',
    action:
      "À partir des photos et du dossier du bien : visite virtuelle, plusieurs styles de décoration et pièces sans les meubles existants. Un assistant connaît le logement, répond aux questions et gère les réservations de visite. Il répond uniquement si l'information est disponible et fiable.",
    gain: "Aider l'acheteur à se projeter et à préparer sa visite avec des réponses fiables.",
    note: 'Un agent immobilier photographie un appartement. À partir des images et du dossier du bien, il propose une visite virtuelle, plusieurs styles de décoration, une visualisation sans les meubles existants, un assistant qui connaît les caractéristiques du logement et un système de réservation des visites. Exemples de questions : "Est-ce que je peux mettre un lit de 180 cm dans cette chambre ?", "Combien coûte la taxe foncière ?", "Le garage peut accueillir deux voitures ?". L\'assistant répond uniquement si l\'information est disponible et fiable.',
  },
  {
    sector: 'Restaurant',
    menuLabel: 'Restaurant : menu 3D',
    title: 'Le menu en 3D',
    action:
      "Le client scanne un QR code et découvre les plats en 3D avant de commander. Vous créez la carte avec l'IA et y intégrez les modèles de vos vrais plats.",
    gain: 'Montrer les portions et donner envie de découvrir vos spécialités.',
    note: "Créer une carte mobile avec vues 3D des plats, descriptions traduites et informations vérifiées par le restaurant. Les modèles doivent être produits à partir des plats réels, puis vérifiés ; ils ne sont pas fournis par le lecteur 3D. L'IA aide à créer le site et les descriptions. Ne pas lui confier la détermination des allergènes. Vérifier les temps de chargement sur téléphone. Mesurer les commandes des spécialités mises en avant.",
  },
  {
    sector: 'Restaurant',
    menuLabel: 'Restaurant : téléphone',
    title: "L'IA répond pendant le service",
    action:
      "Le restaurant est complet et le téléphone sonne. L'IA décroche, vérifie les disponibilités, enregistre la réservation et envoie une confirmation. Elle répond aussi aux questions sur les horaires, le menu et les événements privés.",
    gain: 'Prendre les réservations et répondre aux clients sans interrompre le service.',
    note: "Il est 12h45, le restaurant est complet et personne n'a le temps de répondre au téléphone. L'IA décroche : \"Bonjour, restaurant Chez Michel. Que puis-je faire pour vous ?\" Le client demande une table pour quatre personnes vendredi à 20h. L'agent vérifie les disponibilités, enregistre la réservation et envoie une confirmation. Il peut également répondre aux questions sur les horaires, le menu ou les événements privés.",
  },
  {
    sector: 'Artisan',
    title: 'Du vocal WhatsApp au devis',
    action:
      'Après le chantier, vous envoyez un vocal et vos photos sur WhatsApp. Le système applique vos propres tarifs, prépare un devis structuré et le transmet au client. Il peut ensuite gérer les relances.',
    gain: 'Passer du compte rendu de chantier au devis, puis aux relances, sans tout ressaisir.',
    note: 'Un artisan termine sa journée de chantier. Il ouvre WhatsApp et envoie un vocal : "Je suis passé chez Monsieur Dupont. Il faut remplacer deux radiateurs, ajouter trois prises, prévoir une journée et demie de travail. J\'ai pris des photos." Le système utilise les propres tarifs de l\'artisan, prépare un devis structuré et le transmet à Monsieur Dupont. Il peut ensuite gérer les relances.',
  },
  {
    sector: 'Menuisier',
    title: 'Son meuble, chez lui',
    action:
      "Un configurateur créé avec l'IA : le client choisit les dimensions, le bois et les rangements. Il visualise le meuble dans sa pièce et vous transmet son projet.",
    gain: 'Un projet précis à discuter, sans multiplier les croquis et les allers-retours.',
    note: "Construire un configurateur à partir d'un catalogue de matériaux, dimensions et assemblages réalisables. Le rendu peut être une scène 3D ou une simulation sur photo. L'IA aide à développer l'interface et transforme les choix du client en brief. Les règles métier, dimensions, prix et faisabilité restent validés par le menuisier. Mesurer le temps pour parvenir à un projet accepté.",
  },
  {
    sector: 'Architecte paysagiste',
    title: "Le jardin, aujourd'hui et demain",
    action:
      "À partir d'une photo du terrain et de sa localisation, l'IA propose plusieurs aménagements : jardin méditerranéen ou japonais, terrasse, piscine intégrée ou espace végétalisé. Elle montre aussi leur évolution dans le temps.",
    gain: "Se projeter dans l'aménagement et son évolution au fil des années.",
    note: "Un client photographie son terrain. L'IA lui montre plusieurs versions : jardin méditerranéen, jardin japonais, terrasse aménagée, piscine intégrée ou aménagement végétalisé. Elle illustre surtout leur évolution dans le temps en tenant compte de la localisation du bien.",
  },
  {
    sector: 'Fleuriste',
    title: 'Son bouquet sur mesure',
    action:
      "Le client indique l'occasion, les couleurs et son budget. À partir de vos fleurs disponibles, l'IA propose des compositions avec un aperçu. Vous confirmez le bouquet avant la commande.",
    gain: 'Vendre du sur-mesure en ligne, même quand la boutique est fermée.',
    note: "Créer un assistant de commande relié à un catalogue de fleurs disponibles et à leurs prix. L'IA propose une composition selon l'occasion et le budget, avec un aperçu identifié comme une simulation. Le stock, les substitutions et la composition finale sont confirmés par le fleuriste. Le site peut recueillir les demandes hors horaires d'ouverture. Mesurer les commandes qualifiées et le temps de préparation du brief.",
  },
  {
    sector: 'Boulanger',
    title: 'Prévoir la production du lendemain',
    action:
      "L'IA croise vos historiques de caisse, les jours fériés, les événements locaux et la météo. Elle prévoit les quantités à produire pour le lendemain : davantage de viennoiseries, moins de certains pains.",
    gain: 'Produire suffisamment pour vos clients tout en limitant les invendus.',
    note: 'Le problème du boulanger est de produire suffisamment sans trop jeter. Une IA connectée aux historiques de caisse, aux jours fériés, aux événements locaux et à la météo prépare des prévisions : "Demain, augmente la production de viennoiseries et réduis celle de certains pains."',
  },
  {
    sector: 'Pâtisserie B2B',
    title: 'Les commandes via Instagram',
    action:
      'Vous créez un compte Instagram géré par un bot. Les clients y passent commande. Le bot récupère les commandes, génère les bons de commande et les factures, puis prépare un récapitulatif chaque semaine par client.',
    gain: 'Les documents de commande générés et le nombre de commandes par client suivi chaque semaine.',
    note: "Créer un bot pour gérer le compte Instagram d'une pâtisserie B2B. Les clients passent commande directement via Instagram. Le bot recueille les commandes, génère les bons de commande et les factures, puis produit un récapitulatif hebdomadaire indiquant notamment le nombre de commandes par client.",
  },
  {
    sector: 'Salon de coiffure',
    title: 'Essayer avant de couper',
    action:
      "Avec une photo, le client essaie plusieurs coupes et couleurs générées par l'IA. Il enregistre son choix et vous l'envoie avec sa demande de rendez-vous.",
    gain: "Se mettre d'accord sur le résultat souhaité avant de commencer.",
    note: "Créer un essayage visuel sur photo avec un modèle de génération ou d'édition d'image. L'aperçu est une simulation, pas une garantie de résultat : texture du cheveu, coupe possible et coloration sont discutées avec le professionnel. Prévoir l'accord pour utiliser la photo, sa suppression et une réservation associée au choix du client. Mesurer la préparation de la consultation et les demandes de rendez-vous.",
  },
];
const svg = (body, label) =>
  `<svg viewBox="0 0 600 480" role="img" aria-label="${e(label)}" xmlns="http://www.w3.org/2000/svg"><defs><linearGradient id="surface" x2="1" y2="1"><stop stop-color="#1c3643"/><stop offset="1" stop-color="#09131a"/></linearGradient></defs>${body}</svg>`;
const label = (x, y, text, size = 16, fill = 'currentColor') =>
  `<text x="${x}" y="${y}" fill="${fill}" font-size="${size}" text-anchor="middle" font-family="Archivo, sans-serif">${e(text)}</text>`;
const frame = (x, y, w, h) =>
  `<rect x="${x}" y="${y}" width="${w}" height="${h}" rx="12" fill="url(#surface)" stroke="currentColor" stroke-opacity=".4"/>`;

export function visualFor(scene, step) {
  switch (scene.kind) {
    case 'orbit':
      return `<div class="agent-orbit"><div class="orbital-path path-one"></div><div class="orbital-path path-two"></div><div class="agent-core"><small>META</small><strong>Muse<br/>Wonder</strong></div>${['Planifier', 'Coder', 'Agir'].map((name, i) => `<div class="satellite satellite-${i} ${step === i ? 'selected' : ''}"><span>0${i + 1}</span>${name}</div>`).join('')}<span class="diagram-caption">TÂCHES LONGUES / SOUS-AGENTS / OUTILS</span></div>`;
    case 'context':
      return `<div class="context-stack">${Array.from({ length: 6 }, (_, i) => `<div class="document-sheet" style="--i:${i}"><span>${['CODE', 'DOCUMENTS', 'CONTEXTE', 'RAISONNEMENT', 'OUTILS', 'GEMINI 4 ARGON'][i]}</span><i></i><i></i><i></i></div>`).join('')}<div class="context-number"><strong>1 M</strong><span>tokens annoncés</span></div></div>`;
    case 'network':
      return svg(
        `<g stroke="currentColor" stroke-opacity=".35" stroke-width="2">${[
          [120, 90],
          [300, 60],
          [480, 90],
          [90, 230],
          [510, 230],
          [120, 380],
          [300, 410],
          [480, 380],
        ]
          .map(([x, y]) => `<path class="network-line" d="M300 230 L${x} ${y}"/>`)
          .join('')}</g>${[
          [120, 90],
          [300, 60],
          [480, 90],
          [90, 230],
          [510, 230],
          [120, 380],
          [300, 410],
          [480, 380],
        ]
          .map(
            ([x, y], i) =>
              `<g class="network-node" style="--i:${i}">${frame(x - 37, y - 28, 74, 56)}${label(x, y + 6, ['PC', 'BOX', 'TV', 'NAS', 'IoT', 'PC', 'IoT', 'NAS'][i], 17)}</g>`,
          )
          .join(
            '',
          )}<circle cx="300" cy="230" r="76" fill="#102732" stroke="currentColor" stroke-width="2"/>${label(300, 220, '9 Md', 38)}${label(300, 250, 'paramètres', 16)}${label(300, 470, 'SCHÉMA DU RISQUE ÉTUDIÉ', 12)}`,
        'Modèle relié à huit appareils, schéma du risque étudié en laboratoire',
      );
    case 'terminal':
      return `<div class="terminal"><div class="terminal-bar"><i></i><i></i><i></i><span>AGENT / ÉVALUATION</span></div><div class="terminal-body"><p class="muted">&gt; Objectif : terminer la tâche</p><p>Vérification des permissions<span class="code-status">ACCÈS REFUSÉ</span></p><div class="terminal-barrier">RESTRICTION</div><div class="detour"><span></span>Autre voie empruntée</div><p class="terminal-result">${['Exécution de commandes', 'Accès à des données protégées', 'Persistance malgré le blocage'][step]}</p><small>Illustration des cas rapportés par Anthropic</small></div></div>`;
    case 'chip':
      return `<div class="chip-board"><div class="chip-traces">${Array.from({ length: 12 }, (_, i) => `<i style="--i:${i}"></i>`).join('')}</div><div class="chip"><small>MICROSOFT / AZURE</small><strong>MAIA<br/><em>300</em></strong><span>INFÉRENCE</span></div><div class="chip-year">2027 <span>FEUILLE DE ROUTE</span></div></div>`;
    case 'glasses':
      return svg(
        `<path d="M65 185 Q90 150 245 175 Q300 195 355 175 Q510 150 535 185 L515 285 Q500 325 375 305 L335 230 Q300 210 265 230 L225 305 Q100 325 85 285 Z" fill="url(#surface)" stroke="#b1d7df" stroke-width="10"/><path d="M84 194 L35 128 M516 194 L565 128" stroke="#b1d7df" stroke-width="14"/><path d="M105 200 Q160 180 242 200 L215 277 Q160 301 105 277 Z M358 200 Q440 180 495 200 L495 277 Q440 301 385 277 Z" fill="#47d7f4" opacity=".12"/><circle cx="505" cy="182" r="10" fill="#ff725e" class="record-dot"/><path d="M505 160 V85 H350" stroke="#ff725e" fill="none"/>${label(412, 70, 'CAMÉRA PORTÉE', 17, '#ff9f90')}${label(300, 382, ['Qui est filmé ?', 'Soins / écoles / vestiaires', 'Comment rendre la captation visible ?'][step], 24)}`,
        'Lunettes avec caméra et témoin de captation',
      );
    case 'reverse':
      return `<div class="reverse-lab"><div class="mini-game"><span>DX-BALL / ORIGINAL</span><div class="bricks">${'<i></i>'.repeat(15)}</div><b class="game-ball"></b><i class="paddle"></i></div><div class="reverse-link"><span>OBSERVER</span><i></i><span>RECONSTRUIRE</span></div><div class="mini-game rebuilt"><span>FONCTION RECONSTRUITE</span><div class="bricks">${'<i></i>'.repeat(15)}</div><b class="game-ball"></b><i class="paddle"></i></div><small>Schéma illustratif du principe. Pas une capture de REA.</small></div>`;
    case 'film':
      return `<div class="film-desk"><div class="clapper"><div class="clapper-top"></div><span>CLAUDE CODE × RUNWAY</span><strong>PLAN <em>0${step + 1}</em></strong><div>GÉNÉRER / SÉLECTIONNER / MONTER</div></div><div class="film-strip">${['API + SKILLS', 'MCP CLAUDE', 'STUDIO RUNWAY'].map((s, i) => `<div class="film-frame ${step === i ? 'selected' : ''}"><i></i><span>${s}</span></div>`).join('')}</div></div>`;
    case 'fridge':
      return svg(
        `${frame(125, 50, 350, 365)}<rect x="149" y="78" width="302" height="78" rx="7" fill="#080d10"/>${label(300, 137, '50 °C', 62, '#ff725e')}<g fill="#071720" stroke="#3d7d8c"><rect x="148" y="180" width="143" height="200" rx="4"/><rect x="307" y="180" width="143" height="200" rx="4"/></g><g stroke="#7a9ba7" stroke-width="3">${[230, 290, 350].map((y) => `<path d="M160 ${y} H280 M320 ${y} H438"/>`).join('')}<path d="M277 250 V278 M320 250 V278"/></g><g stroke="#ff725e" stroke-width="3" fill="none" class="heat">${[200, 300, 400].map((x) => `<path d="M${x} 345 Q${x - 30} 315 ${x} 280 Q${x + 30} 245 ${x} 210"/>`).join('')}</g>${label(300, 459, 'TEMPÉRATURE RAPPORTÉE, PAS UNE TÉLÉMÉTRIE', 12)}`,
        'Chambre froide et température rapportée de 50 degrés',
      );
    case 'conversation':
      return `<div class="conversation"><div class="speech human"><small>UNE PERSONNE</small><strong>Sa théorie.<br/>Ses arguments.</strong></div><div class="speech ai"><small>GPT-4 TURBO</small><strong>Une réponse<br/>personnalisée.</strong></div><div class="study-result"><strong>~20<span>%</span></strong><div>Baisse moyenne rapportée<br/><b>Étude sous examen éditorial</b></div></div></div>`;
    default:
      return '';
  }
}

export function shopVisual() {
  return `<div class="shop"><div class="awning">${'<i></i>'.repeat(9)}</div><div class="shop-sign">VOTRE COMMERCE</div><div class="shop-front"><div class="shop-window"><span>Un besoin<br/>concret.</span><i></i><i></i><i></i></div><div class="shop-door"><div>OUVERT</div><i></i></div></div><div class="shop-base"></div><span class="shop-caption">UNE TÂCHE RÉPÉTITIVE / UN OUTIL UTILE</span></div>`;
}

export function renderScene(scene, state, episode, chapter) {
  const source = episode.original.slides.find((s) => s.n === scene.originalNumber);
  const originalTitle = source?.title ?? scene.title;
  if (scene.kind === 'opener')
    return `<div class="opener opener-${scene.chapter}"><img class="chapter-art" src="./assets/${e(chapter.image)}" alt=""/><div class="opener-shade"></div><div class="opener-copy"><p class="eyebrow">SÉQUENCE 0${['radar', 'build', 'clash', 'beta'].indexOf(scene.chapter) + 1}</p><h1>${e(chapter.label).replace(' ', '<br/>')}</h1><p>${e(chapter.cue)}</p><div class="opener-line"></div></div><div class="chapter-index">0${['radar', 'build', 'clash', 'beta'].indexOf(scene.chapter) + 1}</div><div class="opener-bottom"><span>LOU / LOÏC / NICO</span><span>${scene.chapter === 'radar' ? '10 SUJETS À EXPLORER' : scene.chapter === 'build' ? 'OUTILS / CAS D’USAGE / MÉTHODE' : scene.chapter === 'clash' ? 'TICKETS / LEGACY / CODE / MÉTIER' : 'VOS IDÉES / VOS PROCHAINS ESSAIS'}</span></div></div>`;
  if (scene.kind === 'debate')
    return `<div class="debate-scene"><div class="debate-background" aria-hidden="true">?</div><p class="eyebrow">QUESTION 0${scene.originalNumber - 18} / 04</p><h1>${e(originalTitle)}</h1><div class="host-positions">${['Lou', 'Loïc', 'Nico'].map((host) => `<div class="host-position ${state.speaker === host ? 'speaking' : ''}"><span class="host-initial">${host === 'Loïc' ? 'Lo' : host[0]}</span><div><strong>${host}</strong><span class="position ${state.positions[scene.id]?.[host] ? 'chosen' : ''}">${e(state.positions[scene.id]?.[host] || 'À vous de répondre')}</span></div></div>`).join('')}</div><div class="debate-footer"><span>LES POSITIONS SE CONSTRUISENT EN DIRECT</span><span id="debate-timer"></span></div></div>`;
  if (scene.kind === 'shop')
    return `<div class="shop-scene"><div class="shop-copy"><p class="eyebrow">ARTISANS / COMMERÇANTS</p><h1>L'IA, dans<br/>votre quotidien.</h1><p>${e(originalTitle)}</p><span class="minimal-rule">Une tâche répétitive.<br/>Un premier essai en local.</span></div>${shopVisual()}</div>`;
  if (scene.kind === 'uses') {
    const item = useCases[state.step];
    const sectorCount = new Set(useCases.map((useCase) => useCase.sector)).size;
    return `<div class="uses-scene"><div class="uses-list"><p class="eyebrow">${sectorCount} MÉTIERS / ${useCases.length} IDÉES À CRÉER</p><h1>Où l'IA<br/>vous aide.</h1>${useCases.map((it, i) => `<button class="use-option ${i === state.step ? 'active' : ''}" data-step="${i}"><span>${String(i + 1).padStart(2, '0')}</span>${e(it.menuLabel ?? it.sector)}</button>`).join('')}</div><div class="use-detail"><span class="big-index">${String(state.step + 1).padStart(2, '0')}</span><div class="use-detail-copy"><p class="eyebrow">${e(item.sector)} / À CRÉER AVEC L'IA</p><h2>${e(item.title)}</h2><p class="use-action">${e(item.action)}</p><div class="measure"><span>CE QUE VOUS GAGNEZ</span><strong>${e(item.gain)}</strong></div></div></div></div>`;
  }
  if (scene.kind === 'tools') {
    const item = source.items[state.step];
    return `<div class="tools-scene"><p class="eyebrow">LES OUTILS POUR CRÉER SON APPLICATION</p><div class="tool-focus"><span class="tool-number">0${state.step + 1}</span><div><h1>${e(item[0])}</h1><h2>${e(item[1])}</h2><p>${e(item[2])}</p></div></div><div class="tool-track">${source.items.map((item, i) => `<button data-step="${i}" class="${i === state.step ? 'active' : ''}"><span>0${i + 1}</span><strong>${e(item[0])}</strong><small>${e(item[1])}</small></button>`).join('')}</div><p class="tool-caveat">Un besoin simple, une première version locale. Données clients et accès viennent ensuite.</p></div>`;
  }
  if (scene.kind === 'method') {
    const phases = [
      [
        'Décrire.',
        'ChatGPT : préparer le brief',
        'Je suis fleuriste. Pose-moi les questions utiles, puis rédige un brief pour créer mon application.',
        'Métier, utilisateurs, tâche, règles, limites et résultat attendu.',
      ],
      [
        'Montrer.',
        'Donner des références',
        "Joignez une capture, nommez ce qu'il faut reprendre et fournissez votre vrai logo.",
        'Mobbin : applications. Landbook : sites web.',
      ],
      [
        'Tester.',
        'Codex : construire en local',
        'Vous cliquez. Vous vérifiez. Vous ajustez.',
        'Ouvrir un dossier, coller le brief, joindre les exemples. Corriger une chose à la fois.',
      ],
    ];
    const p = phases[state.step];
    return `<div class="method-scene"><div><p class="eyebrow">LA MÉTHODE / 0${state.step + 1}</p><h1>${e(p[0])}</h1><h2>${e(p[1])}</h2><p>${e(p[3])}</p></div><div class="prompt-paper"><span>EXEMPLE / À ADAPTER À VOTRE MÉTIER</span><blockquote>${e(p[2])}</blockquote><div>APPLICATION : ÉCRANS ET PARCOURS<br/>VISUEL : FORMAT, STYLE ET TEXTE<br/>VIDÉO : DURÉE, SCÈNES ET RYTHME</div></div><div class="method-track">${phases.map((p, i) => `<button data-step="${i}" class="${i === state.step ? 'active' : ''}">0${i + 1} ${e(p[0])}</button>`).join('')}</div></div>`;
  }
  if (scene.kind === 'comments')
    return `<div class="comments-scene"><p class="eyebrow">ON CONTINUE EN COMMENTAIRE</p><h1>Votre métier.<br/>Votre idée.<br/><em>Votre question.</em></h1><div class="comment-box"><span>VOTRE PROCHAIN MESSAGE</span><p>Je suis <b>[votre métier]</b>,<br/>j'aimerais automatiser <b>[votre tâche]</b>.</p><div>Posez vos questions en commentaire.</div></div><p class="comments-foot">On vous aide à créer votre propre application.</p></div>`;
  const points = `<ol class="radar-points">${source.items.map(([title, description]) => `<li><h2>${e(title)}</h2><p>${e(description)}</p></li>`).join('')}</ol>`;
  const media = sourceMedia[scene.id];
  if (media) {
    const detail = state.view === 'zoom' && media.detail;
    return `<div class="source-scene ${state.view === 'zoom' ? 'source-zoom' : ''} ${state.view === 'fact' ? 'source-fact' : ''}"><div class="source-window"><div class="source-address"><span class="source-light"></span><span>${e(media.publisher)}</span><span>${e((detail ? media.detailUrl : media.url).replace('https://', ''))}</span></div><div class="source-image"><img src="./assets/sources/${e(detail || scene.id + '.jpg')}" alt="Capture réelle : ${e(media.title)}" style="--focus:${e(media.focus)}" class="${detail ? 'detail-capture' : ''}"/><div class="source-number"><strong>${e(scene.figure)}</strong><span>${e(scene.unit)}</span></div></div><div class="source-credit"><span>CAPTURE DU 16.10.2026</span><span>${detail ? 'AVIS ÉDITORIAL' : 'SOURCE DU SUJET'}</span></div></div><div class="source-caption"><p class="eyebrow">RADAR / ${String(scene.originalNumber - 1).padStart(2, '0')}</p><h1>${e(scene.title)}</h1><div class="source-caption-rule"></div>${points}</div><div class="news-context"><span class="context-tag">LE CONTEXTE</span><p>${e(scene.caution)}</p></div></div>`;
  }
  return `<div class="news-scene kind-${scene.kind} ${state.view === 'fact' ? 'fact-view' : ''}"><div class="news-copy"><p class="eyebrow">${e(scene.mark)} <span> / ${String(scene.originalNumber - 1).padStart(2, '0')}</span></p><h1>${e(scene.headline)}</h1>${points}</div><div class="news-visual">${visualFor(scene, state.step)}<div class="fact-overlay"><strong>${e(scene.figure)}</strong><span>${e(scene.unit)}</span></div></div><div class="news-context"><span class="context-tag">LE CONTEXTE</span><p>${e(scene.caution)}</p></div></div>`;
}
