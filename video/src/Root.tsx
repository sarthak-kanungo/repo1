import {Composition} from 'remotion';
import {Reel, reelDuration, type ReelProps} from './Reel';
import example from '../reels/example.json';

// Only scenes as defaults: render props are merged over these, so a handle or
// theme here would leak into every reel that leaves them out.
const defaults: ReelProps = {scenes: example.scenes};

const FPS = 30;

export const RemotionRoot: React.FC = () => (
  <Composition
    id="Reel"
    component={Reel}
    width={1080}
    height={1920}
    fps={FPS}
    durationInFrames={reelDuration(defaults, FPS)}
    defaultProps={defaults}
    calculateMetadata={({props}: {props: ReelProps}) => ({durationInFrames: reelDuration(props, FPS)})}
  />
);
