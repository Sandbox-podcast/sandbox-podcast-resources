import { registerRoot, Composition } from 'remotion';
import { SandboxIntro } from './sandbox-intro';
import timeline from '../timeline.json';

const Root = () => (
  <Composition
    id="SandboxIntro"
    component={SandboxIntro}
    width={timeline.width}
    height={timeline.height}
    fps={timeline.fps}
    durationInFrames={timeline.durationInFrames}
  />
);
registerRoot(Root);
