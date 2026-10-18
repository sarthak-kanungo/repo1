import {Composition} from 'remotion';
import {Reel, reelDuration, type ReelProps} from './Reel';
import example from '../reels/example.json';

const FPS = 30;

export const RemotionRoot: React.FC = () => (
  <Composition
    id="Reel"
    component={Reel}
    width={1080}
    height={1920}
    fps={FPS}
    durationInFrames={reelDuration(example as ReelProps, FPS)}
    defaultProps={example as ReelProps}
    calculateMetadata={({props}: {props: ReelProps}) => ({durationInFrames: reelDuration(props, FPS)})}
  />
);
