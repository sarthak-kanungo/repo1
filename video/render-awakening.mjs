// Renders the Awakening short and lays a generated soundtrack under it.
// Usage: npm run render:awakening   ->  out/awakening.mp4
//        add -- --audio-only to redo just the soundtrack on an existing render.
import {execFileSync} from 'node:child_process';
import {existsSync, mkdirSync} from 'node:fs';

mkdirSync('out', {recursive: true});
const args = ['remotion', 'render', 'src/index.ts', 'Awakening', 'out/awakening-silent.mp4'];
const preinstalled = '/opt/pw-browsers/chromium_headless_shell-1194/chrome-linux/headless_shell';
if (existsSync(preinstalled)) args.push(`--browser-executable=${preinstalled}`);
if (!process.argv.includes('--audio-only')) execFileSync('npx', args, {stdio: 'inherit'});

// Booms land on the story beats: portal 6.8s into scene 4 (18.8s), mech landing (38.7s),
// sword slashes (41-43.3s), core explosion (48s), title (54.2s).
const boom = (t, amp, hz = 45, decay = 2.5) => `${amp}*sin(2*PI*${hz}*(t-${t}))*exp(-${decay}*(t-${t}))*gte(t,${t})`;
const noise = (t, amp, decay) => `${amp}*(2*random(0)-1)*exp(-${decay}*(t-${t}))*gte(t,${t})`;
const parts = [
  // Low drone that swells through the film.
  '(0.10+0.06*t/60)*sin(2*PI*55*t)*(0.7+0.3*sin(2*PI*0.25*t))',
  '0.05*sin(2*PI*82.5*t)',
  // Marching thumps while the army walks.
  '0.45*sin(2*PI*70*t)*exp(-22*mod(t,0.5))*between(t,6,12)',
  '0.25*sin(2*PI*70*t)*exp(-22*mod(t,0.5))*between(t,18,20)',
  boom(18.8, 0.9, 40, 1.2),
  noise(18.8, 0.25, 2),
  boom(38.7, 1.0, 38, 1.5),
  noise(38.7, 0.3, 3),
  boom(41.0, 0.45, 90, 8),
  boom(41.8, 0.45, 90, 8),
  boom(42.6, 0.45, 90, 8),
  boom(43.4, 0.45, 90, 8),
  boom(48.0, 1.0, 35, 0.9),
  noise(48.0, 0.45, 1.2),
  boom(54.2, 0.7, 50, 1.5),
];
const expr = parts.join('+');
execFileSync(
  'ffmpeg',
  [
    '-loglevel', 'error', '-y',
    '-i', 'out/awakening-silent.mp4',
    '-f', 'lavfi', '-i', `aevalsrc='${expr}':s=44100:d=60`,
    '-filter_complex', '[1]afade=t=in:d=2,afade=t=out:st=57.5:d=2.5,alimiter=limit=0.9[a]',
    '-map', '0:v', '-map', '[a]',
    '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k', '-shortest', '-movflags', '+faststart',
    'out/awakening.mp4',
  ],
  {stdio: 'inherit'},
);
console.log('\nRendered out/awakening.mp4');
