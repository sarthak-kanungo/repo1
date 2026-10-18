// Usage: npm run render -- reels/my-reel.json [out/my-reel.mp4]
import {execFileSync} from 'node:child_process';
import {existsSync} from 'node:fs';
import path from 'node:path';

const input = process.argv[2] ?? 'reels/example.json';
const output = process.argv[3] ?? path.join('out', path.basename(input, '.json') + '.mp4');

const args = ['remotion', 'render', 'src/index.ts', 'Reel', output, `--props=${input}`];
// Cloud sessions ship a Chromium headless shell; use it instead of downloading one.
const preinstalled = '/opt/pw-browsers/chromium_headless_shell-1194/chrome-linux/headless_shell';
if (existsSync(preinstalled)) args.push(`--browser-executable=${preinstalled}`);

execFileSync('npx', args, {stdio: 'inherit'});
console.log(`\nRendered ${output}`);
