import {AbsoluteFill, Easing, Sequence, interpolate, random, spring, useCurrentFrame, useVideoConfig} from 'remotion';

// "AI Megacity Battle: Awakening" - a 60s, 1080x1920 animated short.
// Everything is drawn as SVG silhouettes, so it renders anywhere with no assets.

const W = 1080;
const H = 1920;
const RED = '#ff2a2a';
const BLUE = '#4fd8ff';
const METAL = '#20202c';
// Edge light from the burning sky, so dark armour still reads against the ground.
const RIM = '#8a2a22';
const FONT = 'Inter, FreeSans, sans-serif';
const clamp = {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'} as const;

export const AWAKENING_FRAMES = 1800;

// ---------- world ----------

const Sky: React.FC<{portal?: number}> = ({portal = 0}) => (
  <AbsoluteFill
    style={{background: 'linear-gradient(180deg, #120002 0%, #4d050c 40%, #8a1a12 68%, #1a0203 100%)'}}
  >
    {portal > 0 ? (
      <AbsoluteFill
        style={{
          background: `radial-gradient(circle at 50% 22%, rgba(140,230,255,${0.6 * portal}) 0%, rgba(60,120,255,${
            0.25 * portal
          }) 22%, transparent 55%)`,
        }}
      />
    ) : null}
  </AbsoluteFill>
);

type Building = {x: number; w: number; h: number; broken: number};

const makeSkyline = (seed: string, minH: number, maxH: number): Building[] => {
  const out: Building[] = [];
  let x = -40;
  for (let i = 0; x < W + 40; i++) {
    const w = 60 + random(`${seed}w${i}`) * 120;
    out.push({x, w, h: minH + random(`${seed}h${i}`) * (maxH - minH), broken: random(`${seed}b${i}`)});
    x += w + random(`${seed}g${i}`) * 16;
  }
  return out;
};

const FAR = makeSkyline('far', 450, 1050);
const NEAR = makeSkyline('near', 220, 700);

const buildingPath = (b: Building, base: number) => {
  const top = base - b.h;
  if (b.broken < 0.55) return `M${b.x},${base} L${b.x},${top} L${b.x + b.w},${top} L${b.x + b.w},${base} Z`;
  // Shattered top.
  return `M${b.x},${base} L${b.x},${top + 10} L${b.x + b.w * 0.3},${top - 25} L${b.x + b.w * 0.45},${top + 40} L${
    b.x + b.w * 0.7
  },${top + 5} L${b.x + b.w},${top + 60} L${b.x + b.w},${base} Z`;
};

const Skyline: React.FC<{frame: number; base?: number}> = ({frame, base = 1300}) => (
  <svg width={W} height={H} style={{position: 'absolute'}}>
    {FAR.map((b, i) => (
      <path key={`f${i}`} d={buildingPath(b, base - 60)} fill="#2a0508" />
    ))}
    {NEAR.map((b, i) => {
      const lit: React.ReactNode[] = [];
      const cols = Math.floor(b.w / 24);
      const rows = Math.floor((b.h - 60) / 36);
      for (let c = 0; c < cols; c++) {
        for (let r = 0; r < rows; r++) {
          if (random(`win${i}-${c}-${r}`) < 0.88) continue;
          const on = random(`fl${i}-${c}-${r}-${Math.floor(frame / 5)}`) > 0.2;
          lit.push(
            <rect
              key={`${c}-${r}`}
              x={b.x + 8 + c * 24}
              y={base - b.h + 50 + r * 36}
              width={10}
              height={16}
              fill="#ff8a3a"
              opacity={on ? 0.85 : 0.3}
            />,
          );
        }
      }
      return (
        <g key={`n${i}`}>
          <path d={buildingPath(b, base)} fill="#070405" />
          {lit}
        </g>
      );
    })}
    <rect x={0} y={base} width={W} height={H - base} fill="#050304" />
  </svg>
);

const Embers: React.FC<{frame: number; count?: number; color?: string}> = ({frame, count = 60, color = '#ff9a3a'}) => (
  <svg width={W} height={H} style={{position: 'absolute'}}>
    {Array.from({length: count}).map((_, i) => {
      const speed = 2 + random(`es${i}`) * 5;
      const y = H + 50 - ((frame * speed + random(`ey${i}`) * H) % (H + 100));
      const x = random(`ex${i}`) * W + Math.sin(frame / 20 + i) * 20;
      return <circle key={i} cx={x} cy={y} r={2 + random(`er${i}`) * 4} fill={color} opacity={0.4 + random(`eo${i}`) * 0.5} />;
    })}
  </svg>
);

const Smoke: React.FC<{frame: number}> = ({frame}) => (
  <AbsoluteFill>
    {Array.from({length: 7}).map((_, i) => {
      const x = ((random(`sx${i}`) * W + frame * (0.4 + i * 0.1)) % (W + 600)) - 300;
      const y = 700 + random(`sy${i}`) * 700;
      const r = 300 + random(`sr${i}`) * 250;
      return (
        <div
          key={i}
          style={{
            position: 'absolute',
            left: x - r,
            top: y - r,
            width: r * 2,
            height: r * 2,
            borderRadius: '50%',
            background: 'radial-gradient(circle, rgba(0,0,0,0.45) 0%, transparent 70%)',
          }}
        />
      );
    })}
  </AbsoluteFill>
);

// ---------- characters ----------

// Feet at (0,0), about 220 units tall.
const Robot: React.FC<{x: number; y: number; s: number; eye: string; lookUp?: number; step?: number; fall?: number}> = ({
  x,
  y,
  s,
  eye,
  lookUp = 0,
  step = 0,
  fall = 0,
}) => {
  const leg = Math.sin(step) * 8;
  return (
    <g
      transform={`translate(${x},${y + fall * 40}) scale(${s}) rotate(${fall * 80})`}
      opacity={1 - fall * 0.6}
      stroke={RIM}
      strokeWidth={3}
    >
      <rect x={-28} y={-80 + leg} width={20} height={80 - leg} fill={METAL} />
      <rect x={8} y={-80 - leg} width={20} height={80 + leg} fill={METAL} />
      <path d="M-46,-172 L46,-172 L36,-80 L-36,-80 Z" fill={METAL} />
      <rect x={-64} y={-170} width={18} height={74} rx={6} fill={METAL} />
      <rect x={46} y={-170} width={18} height={74} rx={6} fill={METAL} />
      <g transform={`translate(0,${-lookUp * 6})`}>
        <rect x={-25} y={-220} width={50} height={44} rx={10} fill={METAL} />
        <ellipse cx={0} cy={-202 - lookUp * 10} rx={34} ry={12} fill={eye} opacity={0.35} stroke="none" />
        <rect x={-19} y={-206 - lookUp * 10} width={38} height={8} rx={4} fill={eye} stroke="none" />
      </g>
    </g>
  );
};

const Army: React.FC<{
  frame: number;
  march?: number;
  lookUp?: number;
  blue?: number;
  rows?: number;
  top?: number;
  fallAround?: {x: number; progress: number};
}> = ({frame, march = 1, lookUp = 0, blue = 0, rows = 6, top = 1250, fallAround}) => {
  const robots: React.ReactNode[] = [];
  for (let r = 0; r < rows; r++) {
    const s = 0.3 + r * 0.17;
    const y = top + r * r * 22 + r * 60;
    const gap = 120 * s;
    const shift = ((frame * 2.2 * s * march) % gap) - gap;
    for (let i = 0; i * gap + shift < W + gap; i++) {
      const x = i * gap + shift + (r % 2) * gap * 0.5;
      const threshold = (x / W) * 0.7 + random(`t${r}-${i}`) * 0.3;
      const fall =
        fallAround && Math.abs(x - fallAround.x) < 260 && r >= rows - 2
          ? interpolate(fallAround.progress, [random(`fa${r}-${i}`) * 0.6, random(`fa${r}-${i}`) * 0.6 + 0.3], [0, 1], clamp)
          : 0;
      robots.push(
        <Robot
          key={`${r}-${i}`}
          x={x}
          y={y}
          s={s}
          eye={blue > threshold ? BLUE : RED}
          lookUp={lookUp}
          step={march * (frame / 4 + i + r)}
          fall={fall}
        />,
      );
    }
  }
  return (
    <svg width={W} height={H} style={{position: 'absolute'}}>
      {robots}
    </svg>
  );
};

// Feet at (0,0), about 260 units tall.
const Warrior: React.FC<{x: number; y: number; s: number; frame: number; sword?: number; legsTucked?: number}> = ({
  x,
  y,
  s,
  frame,
  sword = -40,
  legsTucked = 0,
}) => {
  const wave = Math.sin(frame / 6) * 18;
  const handX = 40 + Math.cos((sword * Math.PI) / 180) * 10;
  const handY = -150;
  const len = 170;
  const tipX = handX + Math.cos((sword * Math.PI) / 180) * len;
  const tipY = handY + Math.sin((sword * Math.PI) / 180) * len;
  return (
    <g transform={`translate(${x},${y}) scale(${s})`} stroke={RIM} strokeWidth={2}>
      <path d={`M-22,-205 Q${-70 - wave},-120 ${-95 - wave},${-20 + wave / 2} L-30,-30 Z`} fill="#7a0d10" />
      <path d={`M-20,-95 L-34,${-legsTucked * 40} L-16,${-legsTucked * 40} L-4,-95 Z`} fill="#24242e" />
      <path d={`M4,-95 L22,${-legsTucked * 30} L40,${-legsTucked * 30} L20,-95 Z`} fill="#24242e" />
      <path d="M-30,-200 L30,-200 L24,-92 L-24,-92 Z" fill="#2a2a36" />
      <circle cx={0} cy={-226} r={24} fill="#2a2a36" />
      <rect x={-14} y={-232} width={28} height={6} rx={3} fill={BLUE} opacity={0.8} />
      <path d={`M22,-192 L${handX},${handY}`} stroke="#14141a" strokeWidth={16} strokeLinecap="round" />
      <path d={`M${handX},${handY} L${tipX},${tipY}`} stroke={BLUE} strokeWidth={34} strokeOpacity={0.25} strokeLinecap="round" />
      <path d={`M${handX},${handY} L${tipX},${tipY}`} stroke="#d9f6ff" strokeWidth={9} strokeLinecap="round" />
    </g>
  );
};

// Chest core at (0,0); roughly 1500 units tall.
const Mech: React.FC<{x: number; y: number; s: number; frame: number; core?: number}> = ({x, y, s, frame, core = 1}) => {
  const pulse = 0.75 + Math.sin(frame / 5) * 0.25;
  return (
    <g transform={`translate(${x},${y}) scale(${s})`}>
      <path d="M-120,250 L-200,900 L-90,900 L-30,280 Z" fill="#0b0b10" />
      <path d="M120,250 L200,900 L90,900 L30,280 Z" fill="#0b0b10" />
      <path d="M-260,-220 L260,-220 L180,280 L-180,280 Z" fill="#101018" />
      <path d="M-380,-260 L-250,-260 L-300,300 L-400,250 Z" fill="#0b0b10" />
      <path d="M380,-260 L250,-260 L300,300 L400,250 Z" fill="#0b0b10" />
      <path d="M-90,-420 L90,-420 L70,-240 L-70,-240 Z" fill="#101018" />
      <rect x={-60} y={-360} width={120} height={18} rx={9} fill={BLUE} opacity={core} />
      <circle cx={0} cy={0} r={170 * pulse} fill={BLUE} opacity={0.18 * core} />
      <circle cx={0} cy={0} r={90} fill={BLUE} opacity={0.45 * core} />
      <circle cx={0} cy={0} r={48} fill="#e8fbff" opacity={core} />
    </g>
  );
};

const Portal: React.FC<{frame: number; open: number; cx?: number; cy?: number}> = ({frame, open, cx = 540, cy = 420}) => {
  if (open <= 0) return null;
  const r = 380 * open;
  return (
    <svg width={W} height={H} style={{position: 'absolute'}}>
      <defs>
        <radialGradient id="portalCore">
          <stop offset="0%" stopColor="#ffffff" stopOpacity={0.95} />
          <stop offset="35%" stopColor={BLUE} stopOpacity={0.7} />
          <stop offset="100%" stopColor="#1a3cff" stopOpacity={0} />
        </radialGradient>
      </defs>
      <circle cx={cx} cy={cy} r={r * 1.3} fill="url(#portalCore)" />
      {[1, 0.82, 0.64, 0.46].map((k, i) => (
        <circle
          key={i}
          cx={cx}
          cy={cy}
          r={r * k}
          fill="none"
          stroke={i % 2 ? '#ffffff' : BLUE}
          strokeWidth={6 - i}
          strokeDasharray={`${40 + i * 20} ${18 + i * 6}`}
          transform={`rotate(${frame * (i % 2 ? -1.5 : 2) * (1 + i * 0.3)} ${cx} ${cy})`}
          opacity={0.9}
        />
      ))}
      {random(`bolt${Math.floor(frame / 3)}`) > 0.6
        ? Array.from({length: 2}).map((_, b) => {
            const a = random(`ba${frame}-${b}`) * Math.PI * 2;
            let px = cx + Math.cos(a) * r;
            let py = cy + Math.sin(a) * r;
            let d = `M${px},${py}`;
            for (let k = 0; k < 6; k++) {
              px += Math.cos(a) * 60 + (random(`bx${frame}${b}${k}`) - 0.5) * 80;
              py += Math.sin(a) * 60 + (random(`by${frame}${b}${k}`) - 0.5) * 80;
              d += ` L${px},${py}`;
            }
            return <path key={b} d={d} stroke="#dff7ff" strokeWidth={4} fill="none" opacity={open} />;
          })
        : null}
    </svg>
  );
};

// ---------- effects ----------

const Shake: React.FC<{frame: number; amount: number; children: React.ReactNode}> = ({frame, amount, children}) => (
  <AbsoluteFill
    style={{
      transform: `translate(${(random(`shx${frame}`) - 0.5) * amount}px, ${(random(`shy${frame}`) - 0.5) * amount}px)`,
    }}
  >
    {children}
  </AbsoluteFill>
);

const Zoom: React.FC<{scale: number; originY?: string; children: React.ReactNode}> = ({scale, originY = '50%', children}) => (
  <AbsoluteFill style={{transform: `scale(${scale})`, transformOrigin: `50% ${originY}`}}>{children}</AbsoluteFill>
);

const Flash: React.FC<{opacity: number; color?: string}> = ({opacity, color = '#eafcff'}) =>
  opacity > 0 ? <AbsoluteFill style={{backgroundColor: color, opacity}} /> : null;

const Shockwave: React.FC<{progress: number; cx: number; cy: number; color?: string}> = ({
  progress,
  cx,
  cy,
  color = BLUE,
}) =>
  progress > 0 && progress < 1 ? (
    <svg width={W} height={H} style={{position: 'absolute'}}>
      <ellipse cx={cx} cy={cy} rx={progress * 1400} ry={progress * 420} fill="none" stroke={color} strokeWidth={30 * (1 - progress)} opacity={1 - progress} />
    </svg>
  ) : null;

// Captions sit in Instagram's safe zone (x 90-850, below the top bar).
const Caption: React.FC<{text: string; from: number; to: number}> = ({text, from, to}) => {
  const frame = useCurrentFrame();
  const o = interpolate(frame, [from, from + 12, to - 12, to], [0, 1, 1, 0], clamp);
  if (o <= 0) return null;
  return (
    <div
      style={{
        position: 'absolute',
        top: 300,
        left: 90,
        right: 250,
        textAlign: 'center',
        fontFamily: FONT,
        fontWeight: 800,
        fontSize: 66,
        lineHeight: 1.3,
        color: '#ffffff',
        textShadow: '0 4px 28px rgba(0,0,0,0.9)',
        opacity: o,
        transform: `translateY(${(1 - o) * 20}px)`,
      }}
    >
      {text}
    </div>
  );
};

// ---------- scenes ----------

const S1City: React.FC = () => {
  const f = useCurrentFrame();
  return (
    <AbsoluteFill style={{opacity: interpolate(f, [0, 25], [0, 1], clamp)}}>
      <Zoom scale={interpolate(f, [0, 180], [1.15, 1])}>
        <Sky />
        <Skyline frame={f} />
        <Smoke frame={f} />
        <Embers frame={f} />
      </Zoom>
      <Caption text="साल 2099. मेगा सिटी अब इंसानों की नहीं रही।" from={20} to={175} />
    </AbsoluteFill>
  );
};

const S2Army: React.FC = () => {
  const f = useCurrentFrame();
  return (
    <Shake frame={f} amount={f % 15 < 3 ? 10 : 0}>
      <Zoom scale={interpolate(f, [0, 180], [1, 1.08])} originY="80%">
        <Sky />
        <Skyline frame={f} base={1150} />
        <Smoke frame={f} />
        <Army frame={f} top={1100} />
        <Embers frame={f} count={30} />
      </Zoom>
      <Caption text="10,000 AI रोबोट। एक ही आदेश: खत्म करो।" from={10} to={175} />
    </Shake>
  );
};

const S3Warrior: React.FC = () => {
  const f = useCurrentFrame();
  return (
    <AbsoluteFill>
      <Zoom scale={interpolate(f, [0, 180], [1, 1.12])} originY="65%">
        <Sky />
        <Skyline frame={f} base={1350} />
        <svg width={W} height={H} style={{position: 'absolute'}}>
          <path d="M150,1500 Q540,1250 930,1500 L930,1920 L150,1920 Z" fill="#050304" />
          <Warrior x={540} y={1380} s={2.4} frame={f} sword={-55 + Math.sin(f / 30) * 5} />
        </svg>
        <Embers frame={f} />
      </Zoom>
      <Caption text="और बचा था सिर्फ़ एक योद्धा।" from={15} to={175} />
    </AbsoluteFill>
  );
};

const S4Portal: React.FC = () => {
  const f = useCurrentFrame();
  const {fps} = useVideoConfig();
  const open = spring({frame: f - 25, fps, config: {damping: 14, mass: 1.4}});
  return (
    <Shake frame={f} amount={interpolate(f, [25, 40, 120], [0, 28, 6], clamp)}>
      <Sky portal={open} />
      <Portal frame={f} open={open} />
      <Skyline frame={f} base={1300} />
      <Army frame={f} top={1250} rows={5} />
      <Embers frame={f} color={BLUE} count={40} />
      <Flash opacity={interpolate(f, [25, 30, 45], [0, 0.7, 0], clamp)} />
      <Caption text="फिर... आसमान फट गया।" from={50} to={235} />
    </Shake>
  );
};

const S5Freeze: React.FC = () => {
  const f = useCurrentFrame();
  return (
    <AbsoluteFill>
      <Zoom scale={interpolate(f, [0, 180], [1.05, 1.15])} originY="75%">
        <Sky portal={1} />
        <Portal frame={f + 240} open={0.6} cy={260} />
        <Skyline frame={f} base={1050} />
        <Army
          frame={f}
          top={1000}
          rows={7}
          march={interpolate(f, [0, 15], [1, 0], clamp)}
          lookUp={interpolate(f, [10, 40], [0, 1], clamp)}
          blue={interpolate(f, [85, 150], [0, 1.05], clamp)}
        />
      </Zoom>
      <Caption text="हर रोबोट रुक गया..." from={8} to={85} />
      <Caption text="और उनकी आँखें बदल गईं।" from={90} to={178} />
    </AbsoluteFill>
  );
};

const S6Mech: React.FC = () => {
  const f = useCurrentFrame();
  const coreY = interpolate(f, [0, 190], [-700, 820], {...clamp, easing: Easing.out(Easing.cubic)});
  const land = interpolate(f, [175, 215], [0, 1], clamp);
  return (
    <Shake frame={f} amount={interpolate(f, [170, 180, 230], [2, 34, 0], clamp)}>
      <Sky portal={1} />
      <Portal frame={f + 420} open={0.8} cy={300} />
      <Skyline frame={f} base={1400} />
      <svg width={W} height={H} style={{position: 'absolute'}}>
        <Mech x={540} y={coreY} s={0.62} frame={f} />
      </svg>
      <Army frame={f} top={1420} rows={4} march={0} lookUp={1} blue={2} />
      <Shockwave progress={land} cx={540} cy={1400} />
      <Caption text="कुछ जाग चुका था।" from={20} to={235} />
    </Shake>
  );
};

const S7Battle: React.FC = () => {
  const f = useCurrentFrame();
  const leap = interpolate(f, [130, 230], [0, 1], {...clamp, easing: Easing.out(Easing.quad)});
  const camY = leap * 700;
  const slashes = [25, 50, 75, 100];
  const swordAngle = -60 + (f % 25 < 6 ? 110 : 0);
  return (
    <Shake frame={f} amount={f < 120 && f % 25 < 4 ? 16 : 3}>
      <Sky portal={0.8} />
      <AbsoluteFill style={{transform: `translateY(${camY}px)`}}>
        <svg width={W} height={H} style={{position: 'absolute'}}>
          <Mech x={540} y={150} s={0.5} frame={f} />
        </svg>
        <Skyline frame={f} base={1250} />
        <Army frame={f} top={1250} rows={6} march={0.6} lookUp={0} blue={2} fallAround={{x: 540, progress: interpolate(f, [20, 120], [0, 1], clamp)}} />
        <svg width={W} height={H} style={{position: 'absolute'}}>
          <Warrior
            x={540}
            y={1700 - leap * 1250}
            s={1.6 + leap * 0.3}
            frame={f}
            sword={f < 130 ? swordAngle : -90}
            legsTucked={leap}
          />
          {f < 125
            ? slashes.map((t) => {
                const p = interpolate(f, [t, t + 8], [0, 1], clamp);
                if (p <= 0 || p >= 1) return null;
                return (
                  <path
                    key={t}
                    d={`M${300 + (t % 50) * 4},1450 Q540,${1250 - (t % 3) * 60} ${780 - (t % 50) * 4},1500`}
                    stroke="#e8fbff"
                    strokeWidth={22 * (1 - p)}
                    fill="none"
                    opacity={1 - p}
                  />
                );
              })
            : null}
          {f < 125
            ? Array.from({length: 24}).map((_, i) => {
                const t = slashes.find((s) => f >= s && f < s + 12);
                if (t === undefined) return null;
                const p = (f - t) / 12;
                const a = random(`sp${t}-${i}`) * Math.PI * 2;
                const d = 60 + random(`sd${t}-${i}`) * 260;
                return <circle key={i} cx={540 + Math.cos(a) * d * p} cy={1500 + Math.sin(a) * d * p} r={5} fill="#ffd27a" opacity={1 - p} />;
              })
            : null}
        </svg>
      </AbsoluteFill>
      <Caption text="वो अकेला था... पर हारा नहीं।" from={15} to={235} />
    </Shake>
  );
};

const S8Blast: React.FC = () => {
  const f = useCurrentFrame();
  const pull = interpolate(f, [30, 180], [1.5, 1], {...clamp, easing: Easing.inOut(Easing.cubic)});
  return (
    <Shake frame={f} amount={interpolate(f, [0, 10, 60], [40, 30, 0], clamp)}>
      <Zoom scale={pull} originY="40%">
        <Sky portal={1} />
        <Portal frame={f + 700} open={0.9} cy={380} />
        <Skyline frame={f} base={1350} />
        <svg width={W} height={H} style={{position: 'absolute'}}>
          <g opacity={interpolate(f, [20, 90], [1, 0], clamp)}>
            <Mech x={540} y={900 + f * 3} s={0.5} frame={f} core={interpolate(f, [0, 20], [1, 0], clamp)} />
          </g>
        </svg>
        <Shockwave progress={interpolate(f, [0, 50], [0, 1], clamp)} cx={540} cy={900} />
        <Shockwave progress={interpolate(f, [10, 70], [0, 1], clamp)} cx={540} cy={900} color="#ffffff" />
        <Smoke frame={f} />
        <Embers frame={f} color={BLUE} count={70} />
      </Zoom>
      <Flash opacity={interpolate(f, [0, 4, 40], [1, 1, 0], clamp)} />
      <Caption text="पर पोर्टल... अभी भी खुला है।" from={95} to={178} />
    </Shake>
  );
};

const S9Title: React.FC = () => {
  const f = useCurrentFrame();
  const {fps} = useVideoConfig();
  const t = spring({frame: f - 5, fps, config: {damping: 200}});
  const sub = interpolate(f, [35, 55], [0, 1], clamp);
  const ask = interpolate(f, [75, 95], [0, 1], clamp);
  return (
    <AbsoluteFill style={{background: 'radial-gradient(circle at 50% 40%, #3a0509 0%, #070102 70%)'}}>
      <Embers frame={f + 300} color={BLUE} count={40} />
      <AbsoluteFill style={{justifyContent: 'center', alignItems: 'center', paddingLeft: 90, paddingRight: 250, paddingBottom: 300}}>
        <div style={{fontFamily: FONT, fontSize: 40, letterSpacing: 10, color: '#ff8a7a', opacity: sub, fontWeight: 700}}>
          AI MEGACITY BATTLE
        </div>
        <div
          style={{
            fontFamily: FONT,
            fontWeight: 900,
            fontSize: 118,
            letterSpacing: interpolate(t, [0, 1], [40, 6]),
            color: '#ffffff',
            textShadow: `0 0 40px ${BLUE}`,
            opacity: t,
            marginTop: 20,
            transform: `scale(${0.85 + t * 0.15})`,
          }}
        >
          AWAKENING
        </div>
        <div style={{fontFamily: FONT, fontWeight: 700, fontSize: 52, color: '#ffffff', marginTop: 90, opacity: ask, textAlign: 'center', lineHeight: 1.35}}>
          Part 2 चाहिए?
          <br />
          कमेंट में लिखो: <span style={{color: BLUE}}>YES</span>
        </div>
      </AbsoluteFill>
      <AbsoluteFill style={{backgroundColor: '#000', opacity: interpolate(f, [160, 180], [0, 1], clamp)}} />
    </AbsoluteFill>
  );
};

const SCENES: [React.FC, number][] = [
  [S1City, 180],
  [S2Army, 180],
  [S3Warrior, 180],
  [S4Portal, 240],
  [S5Freeze, 180],
  [S6Mech, 240],
  [S7Battle, 240],
  [S8Blast, 180],
  [S9Title, 180],
];

export const Awakening: React.FC = () => {
  let from = 0;
  return (
    <AbsoluteFill style={{backgroundColor: '#000'}}>
      {SCENES.map(([Scene, frames], i) => {
        const seq = (
          <Sequence key={i} from={from} durationInFrames={frames}>
            <Scene />
          </Sequence>
        );
        from += frames;
        return seq;
      })}
    </AbsoluteFill>
  );
};
