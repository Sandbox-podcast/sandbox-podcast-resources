/** Réglages du détecteur de parole et du réalisateur. Valeurs de départ, à calibrer avec de vraies prises. */
export interface DirectorConfig {
  /** Constante de temps du lissage du niveau, en ms. */
  smoothingMs: number;
  /** Seuil de début de parole, en dBFS. */
  onThresholdDb: number;
  /** Seuil de fin de parole, en dBFS. Plus bas que le seuil de début : c'est l'hystérésis. */
  offThresholdDb: number;
  /** Durée minimale au-dessus du seuil avant de considérer que quelqu'un parle (rejette clics et chocs). */
  minSpeechMs: number;
  /** Durée sous le seuil avant de considérer que la parole est finie (garde les respirations). */
  hangoverMs: number;
  /** Marge, en dB, dont un autre locuteur doit dépasser le dominant pour le remplacer. */
  switchMarginDb: number;
  /** Durée pendant laquelle cette marge doit tenir. */
  switchHoldMs: number;
  /** Durée de parole continue du locuteur actif avant de lui donner un plan serré (rejette toux et interjections). */
  focusAfterMs: number;
  /** Durée minimale d'un plan avant le prochain changement automatique. */
  minShotMs: number;
  /** Durée de chevauchement avant de parler de conversation croisée. */
  crosstalkMs: number;
  /** Durée de silence avant de revenir au plan de groupe. */
  silenceToGroupMs: number;
  /** Fenêtre d'observation pour détecter une conversation à deux. */
  duoWindowMs: number;
  /** Nombre d'alternances de locuteur dans cette fenêtre pour parler de duo. */
  duoMinSwitches: number;
}

export const DEFAULT_CONFIG: DirectorConfig = {
  smoothingMs: 120,
  onThresholdDb: -42,
  offThresholdDb: -48,
  minSpeechMs: 300,
  hangoverMs: 500,
  switchMarginDb: 4,
  switchHoldMs: 350,
  focusAfterMs: 900,
  minShotMs: 2500,
  crosstalkMs: 1200,
  silenceToGroupMs: 4000,
  duoWindowMs: 8000,
  duoMinSwitches: 3,
};
