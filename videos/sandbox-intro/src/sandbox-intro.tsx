import React, { useEffect, useState } from 'react';
import {
  AbsoluteFill,
  Html5Audio,
  Img,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
  delayRender,
  continueRender,
  cancelRender,
} from 'remotion';
import timeline from '../timeline.json';

const C = {
  bg: '#05090d',
  navy: '#0c2333',
  cyan: '#1cb5ed',
  pale: '#f1ecdf',
  red: '#f44943',
  yellow: '#ffce49',
  blue: '#3cd6fc',
  ink: '#071016',
};
const clamp = (n: number, a = 0, b = 1) => Math.min(b, Math.max(a, n));
const ease = (n: number) => 1 - Math.pow(1 - clamp(n), 3);
const pop = (t: number) => (t < 0 ? 0 : 1 - Math.exp(-t * 12) * Math.cos(t * 17));
const wave = (t: number, f = 3, a = 1) => Math.sin(t * f) * a;
type Host = 'lou' | 'loic' | 'nico';
interface TextProps {
  x: number;
  y: number;
  size?: number;
  fill?: string;
  children: React.ReactNode;
  anchor?: 'start' | 'middle' | 'end';
  rotate?: number;
  mono?: boolean;
  stroke?: string;
  fit?: number;
}
const Text = ({
  x,
  y,
  size = 64,
  fill = C.pale,
  children,
  anchor = 'start',
  rotate = 0,
  mono = false,
  stroke,
  fit,
}: TextProps) => (
  <text
    x={x}
    y={y}
    fontFamily={mono ? 'Arial, sans-serif' : 'Anton, Impact, sans-serif'}
    fontWeight={mono ? 700 : 400}
    fontSize={size}
    letterSpacing={mono ? 2 : 0.4}
    fill={fill}
    textAnchor={anchor}
    transform={`rotate(${String(rotate)} ${String(x)} ${String(y)})`}
    stroke={stroke}
    strokeWidth={stroke ? 10 : 0}
    paintOrder="stroke"
    textLength={fit}
    lengthAdjust={fit ? 'spacingAndGlyphs' : undefined}
  >
    {children}
  </text>
);
const Line = ({ d, color = C.pale, width = 8 }: { d: string; color?: string; width?: number }) => (
  <path
    d={d}
    fill="none"
    stroke={color}
    strokeWidth={width}
    strokeLinecap="round"
    strokeLinejoin="round"
  />
);
const Star = ({
  x,
  y,
  r = 140,
  color = C.yellow,
  turn = 0,
}: {
  x: number;
  y: number;
  r?: number;
  color?: string;
  turn?: number;
}) => (
  <polygon
    transform={`rotate(${String(turn)} ${String(x)} ${String(y)})`}
    points={Array.from({ length: 24 }, (_, i) => {
      const a = (i * Math.PI) / 12;
      const l = i % 2 ? r * 0.66 : r;
      return `${String(x + Math.cos(a) * l)},${String(y + Math.sin(a) * l)}`;
    }).join(' ')}
    fill={color}
    stroke={C.ink}
    strokeWidth="7"
  />
);
const Label = ({
  x,
  y,
  w = 330,
  text,
  color = C.cyan,
  angle = -3,
  size = 55,
}: {
  x: number;
  y: number;
  w?: number;
  text: string;
  color?: string;
  angle?: number;
  size?: number;
}) => (
  <g transform={`translate(${String(x)} ${String(y)}) rotate(${String(angle)})`}>
    <path
      d={`M 0 0 L ${String(w)} -7 L ${String(w + 9)} 78 L 5 84 Z`}
      fill={color}
      stroke={C.ink}
      strokeWidth="6"
    />
    <Text x={w / 2} y={59} size={Math.min(size, 65)} fit={w - 48} fill={C.ink} anchor="middle">
      {text}
    </Text>
  </g>
);
const Head = ({
  host,
  x,
  y,
  h = 270,
  angle = 0,
  scale = 1,
  alternate = false,
}: {
  host: Host;
  x: number;
  y: number;
  h?: number;
  angle?: number;
  scale?: number;
  alternate?: boolean;
}) => {
  const ratio =
    host === 'lou' ? 560 / 715 : host === 'loic' ? (alternate ? 566 / 802 : 565 / 700) : 165 / 186;
  const portrait = host === 'loic' && alternate ? 'loic-alt' : host;
  return (
    <g
      transform={`translate(${String(x)} ${String(y)}) rotate(${String(angle)}) scale(${String(scale)})`}
    >
      <image
        href={staticFile(portrait + '.png')}
        x={(-h * ratio) / 2}
        y={-h / 2}
        width={h * ratio}
        height={h}
        filter="url(#sticker)"
      />
    </g>
  );
};
const Actor = ({
  host,
  x,
  y,
  t,
  scale = 1,
  coat = false,
  boxing = false,
  arm = 0,
}: {
  host: Host;
  x: number;
  y: number;
  t: number;
  scale?: number;
  coat?: boolean;
  boxing?: boolean;
  arm?: number;
}) => {
  const color = coat ? C.pale : host === 'lou' ? C.cyan : host === 'loic' ? C.yellow : C.red;
  return (
    <g transform={`translate(${String(x)} ${String(y)}) scale(${String(scale)})`}>
      <ellipse cx="0" cy="444" rx="154" ry="24" fill="#000" opacity=".4" />
      <Line d="M -51 290 L -69 418 L -121 430 M 51 290 L 73 418 L 125 430" width={28} />
      <path
        d="M -62 98 Q -94 105 -105 148 L -83 300 Q 0 325 84 300 L 105 148 Q 91 105 62 98 Z"
        fill={color}
        stroke={C.ink}
        strokeWidth="9"
      />
      {coat ? (
        <>
          <Line d="M -30 106 L 0 165 L 30 106 M 0 165 L 0 300" color={C.ink} width={5} />
          <rect x="32" y="175" width="39" height="35" fill={C.cyan} />
        </>
      ) : (
        <Text x={0} y={223} size={boxing ? 72 : 48} fill={C.ink} anchor="middle">
          {boxing ? 'KO' : host === 'lou' ? 'PM' : 'DEV'}
        </Text>
      )}
      <g transform={`rotate(${String(-15 + arm + wave(t, 7, 7))} -82 142)`}>
        <Line d="M -82 142 L -155 217 L -204 158" color={color} width={33} />
        <circle
          cx="-204"
          cy="158"
          r={boxing ? 45 : 23}
          fill={boxing ? C.red : C.pale}
          stroke={C.ink}
          strokeWidth="6"
        />
      </g>
      <g transform={`rotate(${String(15 - arm + wave(t, 6, 7))} 82 142)`}>
        <Line d="M 82 142 L 157 199 L 211 126" color={color} width={33} />
        <circle
          cx="211"
          cy="126"
          r={boxing ? 45 : 23}
          fill={boxing ? C.cyan : C.pale}
          stroke={C.ink}
          strokeWidth="6"
        />
      </g>
      <Head host={host} x={0} y={0} h={280} angle={wave(t, 5, 3)} alternate={coat || boxing} />
    </g>
  );
};
const Ticket = ({
  x,
  y,
  angle = 0,
  number = 1,
  s = 1,
  stamp = false,
}: {
  x: number;
  y: number;
  angle?: number;
  number?: number;
  s?: number;
  stamp?: boolean;
}) => (
  <g
    transform={`translate(${String(x)} ${String(y)}) rotate(${String(angle)}) scale(${String(s)})`}
  >
    <path
      d="M 0 0 L 261 0 L 286 26 L 286 177 L 0 177 Z"
      fill={C.pale}
      stroke={C.ink}
      strokeWidth="6"
    />
    <path d="M 261 0 L 261 26 L 286 26" fill={C.yellow} stroke={C.ink} strokeWidth="4" />
    <rect x="16" y="18" width="91" height="27" fill={C.cyan} />
    <Text x={23} y={39} size={18} mono fill={C.ink}>
      IA #{String(number).padStart(2, '0')}
    </Text>
    <Line d="M 19 72 L 245 72 M 19 95 L 226 95 M 19 118 L 198 118" color="#85969e" width={8} />
    <Text x={18} y={157} size={24} fit={248} fill={C.ink}>
      FAIRE LE TRUC. EN MIEUX.
    </Text>
    {stamp ? (
      <g transform="rotate(-13 140 90)">
        <rect x="28" y="58" width="233" height="69" fill={C.pale} stroke={C.red} strokeWidth="8" />
        <Text x={143} y={113} size={66} fill={C.red} anchor="middle">
          NON LU
        </Text>
      </g>
    ) : null}
  </g>
);
const Robot = ({ x, y, t, s = 1 }: { x: number; y: number; t: number; s?: number }) => (
  <g transform={`translate(${String(x)} ${String(y)}) scale(${String(s)})`}>
    <Line d="M 0 -100 L 0 -141" color={C.cyan} />
    <circle cy="-152" r="16" fill={C.red} />
    <rect
      x="-103"
      y="-94"
      width="206"
      height="160"
      rx="28"
      fill={C.pale}
      stroke={C.ink}
      strokeWidth="8"
    />
    <rect x="-75" y="-55" width="150" height="64" rx="13" fill={C.ink} />
    <circle cx="-37" cy="-24" r={12 + wave(t, 9, 2)} fill={C.cyan} />
    <circle cx="37" cy="-24" r={12 + wave(t, 9, 2)} fill={C.cyan} />
    <Line d="M -43 37 L 43 37" color={C.ink} width={7} />
    <rect
      x="-74"
      y="81"
      width="148"
      height="115"
      rx="14"
      fill={C.cyan}
      stroke={C.ink}
      strokeWidth="8"
    />
    <Text x={0} y={158} anchor="middle" fill={C.ink} size={60}>
      IA
    </Text>
  </g>
);
const Burst = ({ t, x = 960, y = 600 }: { t: number; x?: number; y?: number }) =>
  t < 0 || t > 1.4 ? null : (
    <g
      opacity={1 - clamp((t - 0.6) / 0.8)}
      transform={`translate(${String(x)} ${String(y)}) scale(${String(pop(t) * 1.5)})`}
    >
      <Star x={0} y={0} r={440 + t * 260} color={C.red} turn={t * 12} />
      <Star x={0} y={0} r={320 + t * 130} color={C.yellow} turn={15 - t * 10} />
      <Text x={0} y={55} size={210} fill={C.ink} anchor="middle" rotate={-7}>
        BOUM !
      </Text>
    </g>
  );
const Header = ({
  name,
  tag,
  color = C.cyan,
  t,
}: {
  name: string;
  tag: string;
  color?: string;
  t: number;
}) => (
  <g transform={`translate(${String((1 - ease(t * 3)) * -250)} 0)`}>
    <Text x={106} y={54} size={25} mono fill={color}>
      {tag}
    </Text>
    <Text x={101} y={280} size={188}>
      {name}
    </Text>
    <path d="M 106 305 L 175 305" stroke={color} strokeWidth="10" />
  </g>
);
const Backdrop = ({ t, color = C.cyan }: { t: number; color?: string }) => (
  <>
    <rect width="1920" height="1080" fill={C.bg} />
    <path d="M -100 870 L 1500 250 L 2080 540 L 2000 1200 L -100 1200 Z" fill={C.navy} />
    <circle cx={1610 + wave(t, 0.6, 25)} cy="290" r="490" fill="url(#dots)" opacity=".35" />
    <path
      d="M 1750 80 L 1820 80 L 1820 150 M 100 940 L 100 1000 L 170 1000"
      fill="none"
      stroke={color}
      strokeWidth="5"
      opacity=".7"
    />
    <path
      d="M -30 1080 L 620 870 L 1960 910"
      fill="none"
      stroke={C.pale}
      strokeWidth="3"
      opacity=".16"
    />
  </>
);

function Intro({ t }: { t: number }) {
  const alert = t >= 7.84;
  const boot = ease((t - 3.1) * 3);
  return (
    <>
      <g transform={`translate(960 480) scale(${String(1 - boot * 0.39)}) translate(-960 -480)`}>
        <Line
          d={`M 440 600 C 160 ${String(600 + wave(t, 5, 70))} 240 1000 25 940 M 1470 670 C 1780 570 1500 1010 1920 860`}
          color={C.cyan}
          width={22}
        />
        <path
          d="M 477 183 L 1460 163 L 1514 800 L 420 800 Z"
          fill={C.pale}
          stroke={C.ink}
          strokeWidth="13"
        />
        <rect
          x="490"
          y="221"
          width="909"
          height="480"
          rx="45"
          fill={alert ? '#6d211f' : C.ink}
          stroke="#879a9e"
          strokeWidth="11"
        />
        <rect x="544" y="269" width="800" height="370" rx="20" fill={alert ? C.red : C.navy} />
        {t < 3.36 ? (
          <g
            transform={`translate(944 456) scale(${String(0.88 + pop(t - 0.65) * 0.1 + pop(t - 2.13) * 0.03)})`}
          >
            <image href={staticFile('logo.png')} x="-390" y="-130" width="780" height="260" />
          </g>
        ) : (
          <>
            <Text x={944} y={326} size={49} fill={alert ? C.pale : C.cyan} anchor="middle">
              {alert ? 'ARRÊT IMPOSSIBLE.' : 'INITIALISATION SANDBOX'}
            </Text>
            {[0, 1, 2].map((i) => (
              <g
                key={i}
                opacity={ease((t - 4.3 - i * 0.65) * 3)}
                transform={`translate(${String(740 + i * 205)} 460)`}
              >
                <circle cy="-5" r="48" fill={alert ? C.yellow : '#364e5d'} />
                <path
                  d="M -70 110 Q -80 35 0 35 Q 80 35 70 110 Z"
                  fill={alert ? C.yellow : '#364e5d'}
                />
                <Text x={0} y={13} size={62} fill={C.ink} anchor="middle">
                  ?
                </Text>
              </g>
            ))}
            <rect x="578" y="606" width={730 * clamp((t - 3.36) / 4)} height="12" fill={C.cyan} />
          </>
        )}
        {[0, 1, 2].map((i) => (
          <circle
            key={i}
            cx={1310 + i * 48}
            cy="750"
            r="13"
            fill={(Math.floor(t * 5) + i) % 3 === 0 ? C.red : C.ink}
          />
        ))}
        <path
          d="M 794 800 L 776 879 L 1114 879 L 1098 800 M 680 880 L 1225 880 L 1300 930 L 620 930 Z"
          fill={C.pale}
          stroke={C.ink}
          strokeWidth="10"
        />
      </g>
      {t >= 3.36 ? (
        <g opacity={boot}>
          <Text x={105} y={180} size={110} fill={C.cyan}>
            2026.
          </Text>
          <Text x={105} y={265} size={66}>
            L'IA EST ENTRE
          </Text>
          <Text x={105} y={335} size={66}>
            DE BONNES MAINS*
          </Text>
          <Text x={110} y={382} size={23} mono fill="#9baebb">
            *AUCUNE VÉRIFICATION.
          </Text>
        </g>
      ) : null}
      {alert ? (
        <>
          <Star x={1560} y={420} r={175 * pop(t - 7.84)} color={C.red} turn={-10} />
          <Text x={1560} y={434} size={96} anchor="middle" rotate={-8}>
            OUPS.
          </Text>
          {(['lou', 'loic', 'nico'] as Host[]).map((host, i) => (
            <Head
              key={host}
              host={host}
              x={640 + i * 340}
              y={740 - wave(t + i, 7, 16)}
              h={310}
              angle={(i - 1) * 13}
              scale={pop(t - 8.1 - i * 0.13)}
            />
          ))}
          <g transform={`translate(960 937) scale(${String(pop(t - 9.2))})`}>
            <rect x="-590" y="-65" width="1180" height="94" fill={C.red} />
            <Text x={0} y={8} size={67} fit={1100} anchor="middle">
              PERSONNE N'A PENSÉ À LES ARRÊTER.
            </Text>
          </g>
        </>
      ) : null}
    </>
  );
}
function Lou({ t }: { t: number }) {
  const count = Math.min(40, 1 + Math.floor(ease((t - 2.1) / 2.86) * 39));
  const punch = t >= 4.96;
  return (
    <>
      <Header name="LOU" tag="01 / LE PRODUCT MANAGER" t={t} />
      <g transform={`translate(490 540) scale(${String(pop(t) * 0.98)})`}>
        <Star x={0} y={0} r={290} color={C.cyan} turn={t * 4} />
      </g>
      <Actor host="lou" x={490} y={482 + wave(t, 5, 9)} t={t} arm={-20} />
      <g transform={`translate(980 ${String(310 + (1 - ease((t - 0.6) * 3)) * 600)}) rotate(3)`}>
        <rect width="720" height="490" fill={C.pale} stroke={C.ink} strokeWidth="10" />
        <rect width="720" height="63" fill={C.cyan} />
        <Text x={24} y={43} size={32} fill={C.ink}>
          TICKET-O-MATIC / IA GÉNÉRATIVE
        </Text>
        <Text x={35} y={128} size={35} fill={C.ink}>
          DÉCRIVEZ VOTRE BESOIN :
        </Text>
        <Text x={35} y={186} size={49} fill={C.ink}>
          « FAIS-MOI 40 TICKETS. »
        </Text>
        <rect x="35" y="223" width="648" height="83" fill={C.ink} />
        <Text x={358} y={283} size={58} fill={C.pale} anchor="middle">
          GÉNÉRER ENCORE
        </Text>
        <Text x={35} y={379} size={32} fill={C.ink}>
          PRODUCTIVITÉ :
        </Text>
        <Text x={670} y={443} size={147} fill={C.ink} anchor="end">
          {count}
        </Text>
      </g>
      {Array.from({ length: 17 }, (_, i) => {
        const u = t - 2.2 - i * 0.13;
        if (u < 0) return null;
        const a = clamp(u / 1.65);
        return (
          <Ticket
            key={i}
            x={1090 - a * (250 + (i % 4) * 150)}
            y={420 - a * 440 + a * a * (730 + i * 19)}
            angle={-a * (22 + i * 11)}
            number={i + 1}
            s={0.65 + (i % 3) * 0.07}
          />
        );
      })}
      {punch ? (
        <g transform={`translate(1260 650) rotate(-7) scale(${String(pop(t - 4.96))})`}>
          <Star x={0} y={0} r={335} color={C.yellow} />
          <Text x={0} y={30} size={270} fill={C.ink} anchor="middle">
            40
          </Text>
          <Text x={0} y={154} size={120} fill={C.ink} anchor="middle">
            TICKETS !
          </Text>
        </g>
      ) : null}
      {t > 5.45
        ? Array.from({ length: 12 }, (_, i) => (
            <Ticket
              key={i}
              x={150 + (i % 6) * 300}
              y={-330 + (t - 5.45) * 1700 - Math.floor(i / 6) * 270}
              angle={wave(i, 3, 25)}
              number={29 + i}
              s={0.9}
            />
          ))
        : null}
    </>
  );
}
function Loic({ t }: { t: number }) {
  const send = clamp((t - 1.68) / 1.3);
  return (
    <>
      <Header name="LOÏC" tag="02 / LE DÉVELOPPEUR" color={C.yellow} t={t} />
      <Actor host="loic" x={1410} y={463 + wave(t, 4, 9)} t={t} arm={25} />
      <g transform={`translate(850 670) rotate(-3)`}>
        <rect
          x="-340"
          y="-300"
          width="680"
          height="390"
          rx="20"
          fill={C.ink}
          stroke={C.pale}
          strokeWidth="12"
        />
        <rect x="-324" y="-284" width="648" height="43" fill={C.cyan} />
        <Text x={-303} y={-254} size={26} fill={C.ink}>
          AGENT IA / PILOTE AUTOMATIQUE
        </Text>
        {Array.from({ length: 7 }, (_, i) => (
          <Text
            key={i}
            x={-300}
            y={-190 + i * 35}
            size={21}
            mono
            fill={i % 3 === 0 ? C.yellow : C.cyan}
          >
            {[
              '> ticket.read() = false',
              '> agent.build("le truc")',
              '  writing code...',
              '  tests: probablement',
              '  + 128 fichiers modifiés',
              '> git commit -m "ça ira"',
              '✓ TERMINÉ. ENFIN, JE CROIS.',
            ][i].slice(0, Math.floor(clamp((t - 1.7 - i * 0.13) * 2) * 34))}
          </Text>
        ))}
        <path
          d="M -340 95 L 340 95 L 430 167 L -430 167 Z"
          fill={C.pale}
          stroke={C.ink}
          strokeWidth="8"
        />
      </g>
      <Robot x={290} y={610 + wave(t, 6, 8)} t={t} />
      {t < 3.3 ? (
        <Ticket
          x={1100 - send * 640}
          y={420 - send * 45}
          s={1 - send * 0.7}
          angle={send * -90}
          number={40}
        />
      ) : null}
      <Line
        d={`M 365 740 L 430 610 L ${String(440 + wave(t, 5, 40))} 472`}
        color={C.yellow}
        width={28}
      />
      <circle cx="430" cy="610" r="28" fill={C.pale} stroke={C.ink} strokeWidth="8" />
      {t >= 4.16 ? (
        <g transform={`translate(275 380) rotate(-13) scale(${String(pop(t - 4.16))})`}>
          <Ticket x={0} y={0} number={40} s={1.7} stamp />
        </g>
      ) : null}
      {t >= 4.16 ? (
        <Label
          x={1020}
          y={886}
          w={630}
          text="MÊME PAS LU LE TICKET."
          color={C.yellow}
          angle={2}
          size={67}
        />
      ) : null}
    </>
  );
}
const Server = ({
  x,
  y,
  t,
  broken = false,
  angle = 0,
}: {
  x: number;
  y: number;
  t: number;
  broken?: boolean;
  angle?: number;
}) => (
  <g transform={`translate(${String(x)} ${String(y)}) rotate(${String(angle)})`}>
    <rect
      x="-100"
      y="-270"
      width="200"
      height="470"
      rx="12"
      fill={C.pale}
      stroke={C.ink}
      strokeWidth="9"
    />
    {[0, 1, 2, 3, 4].map((i) => (
      <g key={i}>
        <rect
          x="-78"
          y={-246 + i * 81}
          width="156"
          height="65"
          fill={broken ? '#6c2224' : C.navy}
        />
        <circle
          cx="-50"
          cy={-214 + i * 81}
          r="10"
          fill={broken ? C.red : Math.floor(t * 8 + i) % 3 === 0 ? C.yellow : C.cyan}
        />
        <Line
          d={`M -20 ${String(-214 + i * 81)} L 52 ${String(-214 + i * 81)}`}
          width={5}
          color={broken ? C.red : '#6f8c9f'}
        />
      </g>
    ))}
  </g>
);
function Nico({ t }: { t: number }) {
  const press = clamp((t - 2) / 0.3);
  const broken = t >= 3.36;
  const boom = t - 6.18;
  if (t > 6.4 && t < 6.52) return <rect width="1920" height="1080" fill="#000" />;
  return (
    <>
      {broken ? (
        <rect width="1920" height="1080" fill="#541921" opacity={0.28 + wave(t, 14, 0.1)} />
      ) : null}
      <Header name="NICO" tag="03 / LE DÉVELOPPEUR" color={C.red} t={t} />
      {[0, 1, 2, 3].map((i) => (
        <Server
          key={i}
          x={
            1090 +
            i * 212 +
            (boom > 0 ? Math.cos(i * 2) * boom * 480 : wave(t + i, broken ? 45 : 2, broken ? 9 : 0))
          }
          y={670 + (boom > 0 ? -boom * 600 + boom * boom * 340 : 0)}
          t={t}
          broken={broken}
          angle={boom > 0 ? (i - 1) * boom * 80 : 0}
        />
      ))}
      <g
        transform={`translate(${String(boom > 0 ? -boom * 1100 : 0)} ${String(boom > 0 ? -boom * 650 : 0)}) rotate(${String(boom > 0 ? -boom * 90 : 0)} 500 550)`}
      >
        <Actor host="nico" x={490} y={478} t={t} arm={-press * 36} />
        <g transform="translate(680 670)">
          <path
            d="M -160 60 L 170 60 L 200 170 L -190 170 Z"
            fill={C.pale}
            stroke={C.ink}
            strokeWidth="9"
          />
          <ellipse cy={44 + press * 24} rx="127" ry="48" fill="#841c25" />
          <ellipse
            cy={20 + press * 24}
            rx="127"
            ry="48"
            fill={C.red}
            stroke={C.ink}
            strokeWidth="8"
          />
          <Text x={0} y={146} size={29} fit={332} fill={C.ink} anchor="middle">
            DEPLOY TO PRODUCTION
          </Text>
        </g>
      </g>
      {broken && boom < 0 ? (
        <>
          <Label
            x={1015}
            y={309}
            w={620}
            text="PRODUCTION DOWN"
            color={C.red}
            angle={-5}
            size={72}
          />
          <Label x={1320} y={820} w={385} text="ERROR 500" color={C.yellow} angle={6} size={75} />
        </>
      ) : null}
      {t >= 4.16 && t < 6.18 ? (
        <g transform={`translate(850 440) scale(${String(pop(t - 4.16))})`}>
          <Star x={0} y={0} r={245} color={C.pale} />
          <Head host="nico" x={0} y={-30} h={350} angle={wave(t, 35, 5)} />
          <Label
            x={-500}
            y={250}
            w={1000}
            text="MAIS ÇA MARCHAIT EN LOCAL !"
            color={C.yellow}
            angle={-3}
            size={88}
          />
        </g>
      ) : null}
      <Burst t={boom} />
      {boom > 0.8 ? (
        <g opacity={ease(boom - 0.8)}>
          <Text x={960} y={470} size={260} anchor="middle" fill={C.red}>
            500
          </Text>
          <Text x={960} y={560} size={75} anchor="middle">
            ÇA VA REDÉMARRER.
          </Text>
          <Text x={960} y={622} size={32} mono anchor="middle" fill="#9baebb">
            ENFIN... NORMALEMENT.
          </Text>
          <g transform={`translate(960 780) rotate(${String(t * 140)})`}>
            <path d="M -60 0 A 60 60 0 1 1 0 60" stroke={C.cyan} strokeWidth="14" fill="none" />
            <polygon points="-75,-10 -40,-10 -58,18" fill={C.cyan} />
          </g>
        </g>
      ) : null}
    </>
  );
}
function Radar({ t }: { t: number }) {
  const obsolete = t >= 3.12;
  return (
    <>
      <Header name="LE RADAR" tag="01 / TOUTE L'ACTUALITÉ DE L'IA" t={t} />
      <g transform={`translate(1270 580) rotate(${String(wave(t, 2, 3))})`}>
        <circle r="365" fill={C.ink} stroke={C.pale} strokeWidth="13" />
        {[100, 190, 280, 340].map((r) => (
          <circle key={r} r={r} fill="none" stroke="#245166" strokeWidth="4" />
        ))}
        <Line d="M -340 0 L 340 0 M 0 -340 L 0 340" color="#245166" width={4} />
        <g transform={`rotate(${String(t * 140 + t * t * 32)})`}>
          <path d="M 0 0 L 0 -335 A 335 335 0 0 1 290 -167 Z" fill={C.cyan} opacity=".22" />
          <Line d="M 0 0 L 0 -335" color={C.cyan} width={8} />
        </g>
        {[
          [150, -190],
          [-180, -50],
          [90, 210],
        ].map(([x, y], i) => (
          <g
            key={i}
            transform={`translate(${String(x)} ${String(y)}) scale(${String(pop(t - 0.4 - i * 0.3))})`}
          >
            <circle r={22 + wave(t + i, 9, 5)} fill={C.yellow} />
            <circle r={39 + wave(t + i, 9, 5)} fill="none" stroke={C.cyan} strokeWidth="3" />
          </g>
        ))}
      </g>
      {['NOUVEAU MODÈLE !', 'ENCORE UN MODÈLE !', 'DÉJÀ UN AUTRE ?'].map((v, i) => (
        <g
          key={i}
          transform={`translate(${String(115 + (1 - ease((t - 0.5 - i * 0.35) * 4)) * -800)} ${String(365 + i * 152)}) rotate(${String(i % 2 ? -3 : 2)})`}
        >
          <rect
            width="650"
            height="124"
            fill={i === 1 ? C.cyan : C.pale}
            stroke={C.ink}
            strokeWidth="7"
          />
          <Text x={30} y={81} size={57} fit={585} fill={C.ink}>
            {v}
          </Text>
        </g>
      ))}
      {obsolete ? (
        <g transform={`translate(1110 560) rotate(-14) scale(${String(pop(t - 3.12))})`}>
          <rect
            x="-620"
            y="-122"
            width="1240"
            height="241"
            fill={C.red}
            stroke={C.pale}
            strokeWidth="12"
          />
          <Text x={0} y={78} size={230} anchor="middle">
            OBSOLÈTE
          </Text>
          <Text x={0} y={202} size={71} anchor="middle">
            DÉJÀ PÉRIMÉ DEMAIN.
          </Text>
        </g>
      ) : null}
    </>
  );
}
function Build({ t }: { t: number }) {
  const zero = t >= 2.8;
  return (
    <>
      <Header name="LE BUILD" tag="02 / ENCORE UN SAAS VIBE-CODÉ" t={t} />
      <g
        transform={`translate(1100 600) rotate(${String(-3 + wave(t, 1, 1))}) scale(${String(pop(t - 0.2))})`}
      >
        <rect
          x="-620"
          y="-260"
          width="1240"
          height="610"
          rx="22"
          fill={C.pale}
          stroke={C.ink}
          strokeWidth="10"
        />
        <rect x="-620" y="-260" width="1240" height="65" rx="22" fill={C.cyan} />
        <Text x={-582} y={-213} size={37} fill={C.ink}>
          MON SAAS RÉVOLUTIONNAIRE™
        </Text>
        <Text x={590} y={-214} size={28} anchor="end" fill={C.ink}>
          PRO / 99 €
        </Text>
        {Array.from({ length: 5 }, (_, i) => (
          <g
            key={i}
            transform={`translate(${String(-540 + i * 105)} 210) scale(1 ${String(ease((t - 0.65 - i * 0.1) * 3))})`}
          >
            <rect
              x="0"
              y={-80 - i * 25}
              width="67"
              height={80 + i * 25}
              fill={i % 2 ? C.cyan : C.navy}
            />
          </g>
        ))}
        <Text x={-540} y={-125} size={31} fill={C.ink}>
          CROISSANCE PRÉVUE*
        </Text>
        <Text x={-540} y={277} size={19} mono fill={C.ink}>
          *DANS MA TÊTE.
        </Text>
        <rect x="80" y="-140" width="470" height="352" rx="10" fill={C.ink} />
        <Text x={315} y={-80} size={37} fit={415} fill={C.pale} anchor="middle">
          UTILISATEURS ACTIFS
        </Text>
        <Text x={315} y={153} size={260} fill={zero ? C.yellow : C.pale} anchor="middle">
          {zero ? '0' : '—'}
        </Text>
        <rect
          x="175"
          y="243"
          width="280"
          height="63"
          fill={zero ? C.yellow : C.cyan}
          stroke={C.ink}
          strokeWidth="5"
        />
        <Text x={315} y={290} size={45} fill={C.ink} anchor="middle">
          REFRESH
        </Text>
        {zero ? (
          <g transform={`translate(${String(380 + wave(t, 9, 7))} ${String(280 + wave(t, 9, 7))})`}>
            <path
              d="M 0 0 L 10 84 L 29 62 L 51 97 L 69 85 L 48 52 L 77 47 Z"
              fill={C.pale}
              stroke={C.ink}
              strokeWidth="5"
            />
          </g>
        ) : null}
      </g>
      <Actor host="lou" x={257} y={655} t={t} scale={0.56} />
      {zero ? (
        <Label
          x={710}
          y={880}
          w={860}
          text="ZÉRO. MÊME APRÈS REFRESH."
          color={C.yellow}
          angle={-3}
          size={79}
        />
      ) : null}
    </>
  );
}
const Bubble = ({
  x,
  y,
  text,
  t,
  color = C.pale,
  w = 550,
}: {
  x: number;
  y: number;
  text: string;
  t: number;
  color?: string;
  w?: number;
}) => (
  <g transform={`translate(${String(x)} ${String(y)}) scale(${String(pop(t))})`}>
    <path
      d={`M 0 0 L ${String(w)} 0 L ${String(w)} 112 L 100 112 L 56 155 L 65 112 L 0 112 Z`}
      fill={color}
      stroke={C.ink}
      strokeWidth="7"
    />
    <Text x={w / 2} y={77} size={50} fit={w - 42} fill={C.ink} anchor="middle">
      {text}
    </Text>
  </g>
);
function Clash({ t }: { t: number }) {
  return (
    <>
      <Header name="LE CLASH" tag="03 / LE DÉBAT CONSTRUCTIF*" color={C.red} t={t} />
      <path
        d="M 310 830 L 1580 830 L 1770 1050 L 150 1050 Z"
        fill={C.pale}
        stroke={C.ink}
        strokeWidth="10"
      />
      {[340, 1580].map((x) => (
        <rect
          key={x}
          x={x}
          y="490"
          width="27"
          height="485"
          fill={C.red}
          stroke={C.ink}
          strokeWidth="5"
        />
      ))}
      <Actor host="lou" x={520 + wave(t, 8, 24)} y={520} t={t} scale={0.82} boxing />
      <Actor host="loic" x={1085 + wave(t + 1, 8, 20)} y={510} t={t + 1} scale={0.82} boxing />
      <Actor host="nico" x={1450 + wave(t + 2, 8, 25)} y={540} t={t + 2} scale={0.74} boxing />
      {[680, 780, 880].map((y, i) => (
        <Line
          key={y}
          d={`M 340 ${String(y)} Q 960 ${String(y + 50)} 1600 ${String(y)}`}
          color={i === 1 ? C.pale : C.red}
          width={12}
        />
      ))}
      {t < 2.16 ? (
        <>
          <Bubble
            x={140}
            y={310}
            text="C'EST PAS DANS LE TICKET !"
            t={t - 0.1}
            w={650}
            color={C.cyan}
          />
          <Bubble
            x={1050}
            y={285}
            text="ÇA MARCHE EN LOCAL !"
            t={t - 0.5}
            w={650}
            color={C.yellow}
          />
          <Bubble x={750} y={580} text="C'EST UNE FEATURE !" t={t - 0.9} color={C.pale} />
        </>
      ) : (
        <g transform={`translate(960 520) rotate(-5) scale(${String(pop(t - 2.16))})`}>
          <path
            d="M -740 -120 L 740 -140 L 720 250 L -720 275 Z"
            fill={C.yellow}
            stroke={C.ink}
            strokeWidth="12"
          />
          <Text x={0} y={40} size={200} fill={C.ink} anchor="middle">
            3 ÉGOS.
          </Text>
          <Text x={0} y={195} size={112} fit={1320} fill={C.ink} anchor="middle">
            0 REMISE EN QUESTION.
          </Text>
        </g>
      )}
    </>
  );
}
function Beta({ t }: { t: number }) {
  const boom = t - 4.14;
  return (
    <>
      <Header name="LA BÊTA" tag="04 / PERSONNE N'A DEMANDÉ ÇA" color={C.yellow} t={t} />
      <g transform={`translate(${String(wave(t, 35, t > 3 ? 10 : 1))} 0)`}>
        <path
          d="M 550 770 L 1550 770 L 1590 955 L 510 955 Z"
          fill={C.pale}
          stroke={C.ink}
          strokeWidth="12"
        />
        <rect
          x="710"
          y="410"
          width="620"
          height="365"
          rx="40"
          fill={C.navy}
          stroke={C.pale}
          strokeWidth="12"
        />
        <path
          d="M 770 405 L 770 330 Q 770 290 825 290 L 1210 290 Q 1270 290 1270 330 L 1270 405"
          fill="none"
          stroke={C.cyan}
          strokeWidth="28"
        />
        <circle cx="1020" cy="568" r="125" fill={C.ink} stroke={C.yellow} strokeWidth="13" />
        <g transform={`translate(1020 568) rotate(${String(t * 120 + t * t * 26)})`}>
          <Line d="M -90 0 L 90 0 M 0 -90 L 0 90" color={C.cyan} width={14} />
          <circle r="36" fill={C.red} />
        </g>
        <Text x={1020} y={728} size={28} fit={550} anchor="middle">
          MÉLANGEUR À MAUVAISES IDÉES
        </Text>
        {[0, 1, 2, 3].map((i) => (
          <circle
            key={i}
            cx={710 + i * 150}
            cy="844"
            r="18"
            fill={(Math.floor(t * 8) + i) % 3 === 0 ? C.red : C.cyan}
          />
        ))}
        <Robot x={1460} y={400} t={t} s={0.55} />
        <Text
          x={570 + wave(t, 4, 15)}
          y={400 + wave(t, 5, 20)}
          size={100}
          fill={C.cyan}
          rotate={-17}
        >
          {'</>'}
        </Text>
        <g
          transform={`translate(1030 ${String(270 + wave(t, 8, 9))}) rotate(${String(wave(t, 4, 10))})`}
        >
          <path
            d="M -35 0 Q -60 -120 0 -170 Q 60 -120 35 0 L 0 -25 Z"
            fill={C.pale}
            stroke={C.ink}
            strokeWidth="6"
          />
          <circle cy="-100" r="19" fill={C.cyan} />
          <path d="M -23 0 L 0 54 L 23 0" fill={C.red} />
        </g>
      </g>
      {(['lou', 'loic', 'nico'] as Host[]).map((host, i) => (
        <g
          key={host}
          transform={
            boom > 0
              ? `translate(${String((i - 1) * boom * 1600)} ${String(-boom * 1100)}) rotate(${String((i - 1) * boom * 150)} ${String(350 + i * 600)} 650)`
              : undefined
          }
        >
          <Actor
            host={host}
            x={i === 0 ? 340 : i === 1 ? 1540 : 1110}
            y={i === 2 ? 840 : 590}
            t={t + i}
            scale={i === 2 ? 0.43 : 0.58}
            coat
          />
        </g>
      ))}
      {t >= 2.8 ? (
        <Label
          x={570}
          y={906}
          w={1000}
          text="PROBABILITÉ DE SUCCÈS : 1 %"
          color={C.yellow}
          angle={-2}
          size={83}
        />
      ) : null}
      <Burst t={boom} y={570} />
    </>
  );
}
function Finale({ t }: { t: number }) {
  const stopped = t >= 5.12;
  const motion = stopped ? 5.12 : t;
  return (
    <>
      {!stopped ? (
        <>
          {[0, 1, 2, 3, 4, 5, 6, 7].map((i) => (
            <g key={i} transform={`translate(960 530) rotate(${String(i * 45 + motion * 12)})`}>
              <path
                d="M 240 -32 L 1100 -65 L 1100 65 L 240 32 Z"
                fill={i % 2 ? C.cyan : C.pale}
                opacity=".08"
              />
            </g>
          ))}
          <Ticket
            x={100 + wave(motion, 3, 30)}
            y={150}
            angle={-16 - motion * 3}
            s={0.8}
            number={40}
          />
          <Robot x={1660} y={215 + wave(motion, 3, 20)} s={0.65} t={motion} />
          <Label x={1380} y={820} w={350} text="ERROR 500" color={C.red} angle={12} />
          <Text x={140} y={880} size={170} fill={C.yellow} rotate={-10}>
            0 USER
          </Text>
          {(['lou', 'loic', 'nico'] as Host[]).map((host, i) => (
            <Head
              key={host}
              host={host}
              x={960 + (i - 1) * (650 - 350 * ease(t / 1.2))}
              y={275 + wave(motion + i, 5, 18)}
              h={250}
              angle={(i - 1) * 10 + wave(motion + i, 3, 5)}
              scale={pop(t - i * 0.1)}
            />
          ))}
        </>
      ) : null}
      <g
        transform={`translate(960 ${String(stopped ? 375 : 540)}) scale(${String(stopped ? 1 : pop(t - 0.14) * (1 + wave(motion, 6, 0.018)))})`}
      >
        <image href={staticFile('logo.png')} x="-850" y="-283.333" width="1700" height="566.667" />
      </g>
      {!stopped ? (
        <>
          <Text x={960} y={791} size={68} anchor="middle" fill={C.cyan}>
            L'INTELLIGENCE ARTIFICIELLE.
          </Text>
          <Text x={960} y={861} size={68} anchor="middle">
            LES PROBLÈMES HUMAINS.
          </Text>
        </>
      ) : (
        <>
          <Text x={960} y={640} size={92} fit={1430} anchor="middle">
            {t >= 5.12 ? "L'ÉMISSION QUI N'AURAIT" : ''}
          </Text>
          <Text x={960} y={758} size={98} fit={1570} anchor="middle" fill={C.cyan}>
            {t >= 6.64 ? 'JAMAIS DÛ PASSER EN PROD.' : ''}
          </Text>
          {t >= 7.68 ? (
            <g>
              <rect x="818" y="848" width="284" height="63" fill={C.red} />
              <Text x={960} y={894} size={46} anchor="middle" fill={C.ink}>
                ERROR 500
              </Text>
            </g>
          ) : null}
        </>
      )}
    </>
  );
}

const scenes: Record<string, React.FC<{ t: number }>> = {
  intro: Intro,
  lou: Lou,
  loic: Loic,
  nico: Nico,
  radar: Radar,
  build: Build,
  clash: Clash,
  beta: Beta,
  finale: Finale,
};
export function SandboxIntro() {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = frame / fps;
  const [fontHandle] = useState(() => delayRender('Chargement de la typographie'));
  useEffect(() => {
    const font = new FontFace('Anton', `url(${staticFile('Anton-Regular.woff2')})`);
    font
      .load()
      .then((loaded) => {
        document.fonts.add(loaded);
        continueRender(fontHandle);
      })
      .catch(cancelRender);
  }, [fontHandle]);
  const current = timeline.scenes.find((s) => t >= s.start && t < s.end) ?? timeline.scenes[8];
  const Scene = scenes[current.id];
  return (
    <AbsoluteFill style={{ background: C.bg }}>
      <Html5Audio src={staticFile(timeline.audio.replace(/^public\//, ''))} />
      {['lou.png', 'loic.png', 'loic-alt.png', 'nico.png', 'logo.png'].map((src) => (
        <Img
          key={src}
          src={staticFile(src)}
          style={{ position: 'absolute', width: 1, height: 1, opacity: 0 }}
        />
      ))}
      <svg width="1920" height="1080" viewBox="0 0 1920 1080" xmlns="http://www.w3.org/2000/svg">
        <defs>
          <pattern id="dots" width="24" height="24" patternUnits="userSpaceOnUse">
            <circle cx="12" cy="12" r="2.3" fill={C.cyan} />
          </pattern>
          <filter id="sticker" x="-20%" y="-20%" width="140%" height="150%">
            <feMorphology in="SourceAlpha" operator="dilate" radius="3" result="dilated" />
            <feFlood floodColor={C.pale} />
            <feComposite in2="dilated" operator="in" result="outline" />
            <feMerge>
              <feMergeNode in="outline" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
        </defs>
        <Backdrop t={current.id === 'finale' && t >= 56.8 ? 56.8 : t} />
        <Scene t={t - current.start} />
      </svg>
    </AbsoluteFill>
  );
}
