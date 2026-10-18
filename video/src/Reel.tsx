import {
  AbsoluteFill,
  Sequence,
  interpolate,
  spring,
  useCurrentFrame,
  useVideoConfig,
} from 'remotion';

export type Scene = {
  // On-screen text. Keep it short: 3-8 words reads at a glance.
  text: string;
  // Optional smaller line under the main text.
  sub?: string;
  seconds: number;
};

export type ReelProps = {
  theme?: {background?: string; text?: string; accent?: string};
  // Small label shown on every scene, e.g. your @handle.
  handle?: string;
  scenes: Scene[];
};

const DEFAULT_THEME = {background: '#0f0f14', text: '#ffffff', accent: '#ff6b4a'};

export const reelDuration = (props: ReelProps, fps: number) =>
  Math.max(1, Math.round(props.scenes.reduce((sum, s) => sum + s.seconds, 0) * fps));

const SceneView: React.FC<{scene: Scene; index: number; frames: number; theme: typeof DEFAULT_THEME}> = ({
  scene,
  index,
  frames,
  theme,
}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const enter = spring({frame, fps, config: {damping: 200}, durationInFrames: 12});
  const exit = interpolate(frame, [frames - 6, frames], [1, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  // The first scene is the hook: bigger, and it lands harder.
  const isHook = index === 0;
  const parts = scene.text.split(/(\*[^*]+\*)/).filter(Boolean);

  return (
    <AbsoluteFill
      style={{
        justifyContent: 'center',
        alignItems: 'center',
        padding: 90,
        opacity: exit,
      }}
    >
      <div
        style={{
          fontFamily: 'Inter, Helvetica, Arial, sans-serif',
          fontWeight: 800,
          fontSize: isHook ? 112 : 92,
          lineHeight: 1.1,
          color: theme.text,
          textAlign: 'center',
          transform: `translateY(${(1 - enter) * 60}px) scale(${0.92 + enter * 0.08})`,
          opacity: enter,
        }}
      >
        {parts.map((part, i) => {
          // Text wrapped in *asterisks* gets the accent colour.
          const accent = part.startsWith('*') && part.endsWith('*') && part.length > 1;
          return (
            <span key={i} style={{color: accent ? theme.accent : undefined}}>
              {accent ? part.slice(1, -1) : part}
            </span>
          );
        })}
      </div>
      {scene.sub ? (
        <div
          style={{
            marginTop: 40,
            fontFamily: 'Inter, Helvetica, Arial, sans-serif',
            fontWeight: 500,
            fontSize: 52,
            color: theme.text,
            opacity: 0.75 * enter,
            textAlign: 'center',
          }}
        >
          {scene.sub}
        </div>
      ) : null}
    </AbsoluteFill>
  );
};

export const Reel: React.FC<ReelProps> = (props) => {
  const {fps, durationInFrames} = useVideoConfig();
  const frame = useCurrentFrame();
  const theme = {...DEFAULT_THEME, ...props.theme};
  let from = 0;

  return (
    <AbsoluteFill style={{backgroundColor: theme.background}}>
      {props.scenes.map((scene, i) => {
        const frames = Math.round(scene.seconds * fps);
        const seq = (
          <Sequence key={i} from={from} durationInFrames={frames}>
            <SceneView scene={scene} index={i} frames={frames} theme={theme} />
          </Sequence>
        );
        from += frames;
        return seq;
      })}
      {/* Progress bar keeps people watching to the end. */}
      <div
        style={{
          position: 'absolute',
          top: 0,
          left: 0,
          height: 14,
          width: `${(frame / durationInFrames) * 100}%`,
          backgroundColor: theme.accent,
        }}
      />
      {props.handle ? (
        <div
          style={{
            position: 'absolute',
            bottom: 260,
            width: '100%',
            textAlign: 'center',
            fontFamily: 'Inter, Helvetica, Arial, sans-serif',
            fontSize: 40,
            color: theme.text,
            opacity: 0.6,
          }}
        >
          {props.handle}
        </div>
      ) : null}
    </AbsoluteFill>
  );
};
