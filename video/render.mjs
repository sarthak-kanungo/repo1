// Usage: npm run render -- reels/my-reel.json [out/my-reel.mp4] [--transparent]
// --transparent renders a ProRes 4444 .mov with alpha, for laying over footage.
import {execFileSync} from 'node:child_process';
import {existsSync} from 'node:fs';
import path from 'node:path';

const transparent = process.argv.includes('--transparent');
const [input = 'reels/example.json', outArg] = process.argv.slice(2).filter((a) => !a.startsWith('--'));
const output = outArg ?? path.join('out', path.basename(input, '.json') + (transparent ? '.mov' : '.mp4'));

const args = ['remotion', 'render', 'src/index.ts', 'Reel', output, `--props=${input}`];
if (transparent) {
  args.push('--codec=prores', '--prores-profile=4444', '--image-format=png', '--pixel-format=yuva444p10le');
}
// Cloud sessions ship a Chromium headless shell; use it instead of downloading one.
const preinstalled = '/opt/pw-browsers/chromium_headless_shell-1194/chrome-linux/headless_shell';
if (existsSync(preinstalled)) args.push(`--browser-executable=${preinstalled}`);

execFileSync('npx', args, {stdio: 'inherit'});
console.log(`\nRendered ${output}`);
