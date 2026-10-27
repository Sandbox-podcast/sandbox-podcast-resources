(() => {
  const config = window.JINGLE_CONFIG;
  if (!config) throw new Error('Missing JINGLE_CONFIG');

  const stage = document.querySelector('#stage');
  const image = document.querySelector('#hero-image');
  const title = document.querySelector('#hero-title');
  const titleLead = document.querySelector('#title-lead');
  const titleWord = document.querySelector('#title-word');
  const finalTitle = document.querySelector('#final-title');
  const waves = document.querySelector('#wave-form');
  const barSets = [];
  const clamp = (value, min = 0, max = 1) => Math.min(max, Math.max(min, value));
  const mix = (from, to, amount) => from + (to - from) * amount;
  const smooth = (from, to, time) => {
    const x = clamp((time - from) / (to - from));
    return x * x * (3 - 2 * x);
  };
  const out = (from, to, time) => {
    const x = clamp((time - from) / (to - from));
    return 1 - Math.pow(1 - x, 4);
  };
  const wave = (time, seed) => {
    const low = Math.sin(time * 8.2 + seed * 1.4);
    const high = Math.sin(time * 14.9 + seed * 2.8) * 0.42;
    const detail = Math.sin(time * 22.7 + seed * 0.74) * 0.22;
    return Math.abs(low + high + detail) / 1.64;
  };

  stage.dataset.variant = config.variant;
  stage.dataset.duration = String(config.duration);
  document.querySelector('#division-mark').textContent = config.railLabel;
  const makeGlyphs = (container, text, small = false, offset = 0) => {
    container.replaceChildren();
    for (const [index, character] of [...text].entries()) {
      const glyph = document.createElement('span');
      glyph.className = `title-glyph${small ? ' title-glyph-small' : ''}`;
      glyph.style.setProperty('--tile-color', config.tiles[(index + offset) % config.tiles.length]);
      glyph.textContent = character;
      container.append(glyph);
    }
  };
  makeGlyphs(titleLead, config.lead, true);
  finalTitle.innerHTML = `<span class="title-lead">${config.lead}</span><span>${config.word}</span>`;
  for (const [index, character] of [...config.word].entries()) {
    const glyph = document.createElement('span');
    glyph.className = 'title-glyph';
    if (config.accentIndexes.includes(index)) glyph.classList.add('is-accent');
    glyph.style.setProperty(
      '--tile-color',
      config.tiles[(index + config.lead.length) % config.tiles.length],
    );
    glyph.textContent = character === ' ' ? '\u00a0' : character;
    titleWord.append(glyph);
  }
  image.src = `assets/${config.heroFile ?? 'hero.png'}`;
  document.querySelector('#brand-logo').src = 'assets/sandbox-logov2.png';

  if (config.variant === 'clash') {
    for (const side of ['left', 'right']) {
      const row = document.createElement('div');
      row.className = `wave-row ${side}`;
      for (let index = 0; index < 38; index += 1) {
        const bar = document.createElement('span');
        bar.className = 'wave-bar';
        row.append(bar);
        barSets.push({ element: bar, seed: index + (side === 'right' ? 40 : 0) });
      }
      waves.append(row);
    }
  }

  const motifs = {
    radar: document.querySelector('#radar-motif'),
    build: document.querySelector('#build-motif'),
    clash: document.querySelector('#clash-motif'),
    beta: document.querySelector('#beta-motif'),
  };

  window.renderAt = (time) => {
    const t = clamp(time, 0, config.duration);
    const reveal = smooth(0.25, 1.45, t);
    const finale = smooth(config.finaleStart, config.finaleStart + 0.76, t);
    const titleProgress = out(config.mainHit - 0.56, config.mainHit + 0.32, t);
    const beat = Math.max(0, ...config.hits.map((hit) => Math.exp(-Math.abs(t - hit) * 11.5)));

    const drift = mix(1.115, 1.035, smooth(0, config.duration * 0.78, t));
    const directional =
      config.variant === 'radar'
        ? `translate(${mix(7, -8, t / config.duration)}px, ${mix(4, -5, t / config.duration)}px)`
        : config.variant === 'build'
          ? `translate(${mix(-12, 3, t / config.duration)}px, ${mix(13, -4, t / config.duration)}px)`
          : config.variant === 'clash'
            ? `translate(${mix(-10, 10, t / config.duration)}px, ${Math.sin(t * 0.62) * 4}px)`
            : `translate(${Math.sin(t * 0.34) * 8}px, ${mix(9, -3, t / config.duration)}px)`;
    image.style.transform = `${directional} scale(${drift + beat * 0.008})`;
    image.style.filter = 'saturate(0.86) brightness(0.76)';
    image.style.opacity = String(mix(0.68, 1, reveal) * (1 - finale * 0.94));
    document.querySelector('.hero-wash').style.opacity = String(mix(1, 0.78, reveal));
    document.querySelector('.top-rail').style.opacity = String(smooth(0.18, 1.2, t) * (1 - finale));
    document.querySelector('.rail-rule').style.transform = `scaleX(${smooth(0.22, 1.15, t)})`;
    document.querySelector('.edge-frame').style.clipPath =
      `inset(0 ${mix(50, 0, smooth(0.42, 1.55, t))}% 0 ${mix(50, 0, smooth(0.42, 1.55, t))}%)`;
    document.querySelector('.grid-wash').style.opacity = String(0.13 + beat * 0.05);

    for (const [name, element] of Object.entries(motifs)) {
      element.style.opacity =
        name === config.variant
          ? String((0.3 + reveal * 0.55 + beat * 0.12) * (1 - finale * 0.85))
          : '0';
    }
    document.querySelector('.radar-sweep').style.transform =
      `rotate(${t * 48}deg) scale(${1 + beat * 0.014})`;
    document.querySelector('.radar-sweep').style.opacity =
      config.variant === 'radar' ? String(0.36 + reveal * 0.44) : '0';
    document.querySelector('.build-scaffold').style.transform =
      `translateX(-50%) perspective(1300px) rotateY(${mix(-22, -9, reveal)}deg) rotateX(${mix(11, 3, reveal)}deg) translateY(${mix(55, 0, reveal)}px) scale(${mix(0.88, 1, reveal) + beat * 0.018})`;
    document.querySelector('.build-scaffold').style.opacity =
      config.variant === 'build' ? String(0.35 + reveal * 0.45) : '0';
    document.querySelectorAll('.beta-orbit').forEach((element, index) => {
      element.style.transform = `rotate(${t * (index === 0 ? 31 : -23)}deg) scale(${1 + beat * 0.017})`;
    });
    document.querySelectorAll('.beta-bracket').forEach((element, index) => {
      element.style.opacity =
        config.variant === 'beta'
          ? String(0.45 + reveal * 0.45 + beat * (0.15 + (index % 2) * 0.07))
          : '0';
      element.style.transform = `scale(${mix(0.76, 1, reveal) + beat * 0.04})`;
    });
    document.querySelectorAll('.clash-side-wash').forEach((element, index) => {
      element.style.transform = `translateX(${mix(index === 0 ? -55 : 55, 0, reveal)}px)`;
      element.style.opacity =
        config.variant === 'clash' ? String(0.2 + reveal * 0.5 + beat * 0.18) : '0';
    });
    for (const { element, seed } of barSets) {
      const amplitude = wave(t, seed) * (0.3 + reveal * 0.55 + beat * 0.26);
      element.style.transform = `scaleY(${0.2 + amplitude})`;
      element.style.opacity = String(0.42 + amplitude * 0.58);
    }

    title.style.opacity = String(titleProgress * (1 - finale));
    title.style.transform = `translateY(${mix(180, 0, titleProgress) - beat * 4}px) scale(${mix(0.88, 1, titleProgress) + beat * 0.018})`;
    document.querySelector('.title-kicker').style.opacity = String(titleProgress);
    document.querySelector('.title-trail').style.transform =
      `scaleX(${out(config.mainHit + 0.16, config.mainHit + 0.72, t)})`;
    document.querySelectorAll('.title-glyph').forEach((element, index) => {
      const glyphProgress = out(
        config.mainHit - 0.56 + index * 0.052,
        config.mainHit + 0.05 + index * 0.052,
        t,
      );
      element.style.opacity = String(glyphProgress);
      element.style.transform = `translateY(${mix(154, 0, glyphProgress)}px) rotate(${mix(index % 2 ? 13 : -12, index % 2 ? -2 : 2, glyphProgress)}deg) scale(${mix(0.72, 1, glyphProgress)})`;
    });
    const flash = Math.max(
      0,
      ...config.hits.map((hit) => Math.max(0, 1 - Math.abs(t - hit) / 0.11)),
    );
    document.querySelector('.impact-flash').style.opacity = String(flash * 0.13);

    const endCard = document.querySelector('.end-card');
    endCard.style.opacity = String(finale);
    const finalTextProgress = out(config.finaleStart + 0.2, config.finaleStart + 0.85, t);
    document.querySelector('.final-title').style.opacity = String(finalTextProgress);
    document.querySelector('.final-title').style.transform =
      `translateY(${mix(34, 0, finalTextProgress)}px) scale(${mix(0.94, 1, finalTextProgress)})`;
    document.querySelector('.logo-mask').style.opacity = String(
      out(config.finaleStart + 0.72, config.finaleStart + 1.28, t),
    );
    document.querySelector('.logo-mask').style.clipPath =
      `inset(0 ${mix(50, 0, out(config.finaleStart + 0.72, config.finaleStart + 1.28, t))}% 0 ${mix(50, 0, out(config.finaleStart + 0.72, config.finaleStart + 1.28, t))}%)`;
    document.querySelector('.logo-mask').style.transform =
      `scale(${mix(0.96, 1, out(config.finaleStart + 0.72, config.finaleStart + 1.28, t))})`;
    document.querySelector('.final-rule').style.transform =
      `scaleX(${out(config.finaleStart + 0.45, config.finaleStart + 1.05, t)})`;
    document.querySelector('.end-card').style.setProperty('--end-reveal', String(finale));
    document.querySelector('.bottom-scan').style.transform =
      `scaleX(${smooth(0.18, config.duration, t)})`;
    document
      .querySelector('.bottom-scan')
      .style.setProperty('--scan-progress', String(clamp(t / config.duration)));
    document.documentElement.dataset.time = t.toFixed(3);
  };

  const fitStage = () => {
    const scale = Math.min(window.innerWidth / 1920, window.innerHeight / 1080);
    stage.style.setProperty('--fit', String(scale));
  };
  fitStage();
  window.addEventListener('resize', fitStage);
  document.fonts.ready.then(() => {
    if (!new URLSearchParams(window.location.search).has('render')) {
      let start = performance.now();
      const tick = (now) => {
        window.renderAt((now - start) / 1000);
        if ((now - start) / 1000 < config.duration) requestAnimationFrame(tick);
      };
      requestAnimationFrame(tick);
    } else {
      window.renderAt(0);
      window.__JINGLE_READY__ = true;
    }
  });
})();
