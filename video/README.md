# Reel videos with Remotion

Renders vertical (1080x1920, 30fps) text-animation videos from a JSON script.
A free alternative to Claude Motion for plans that do not include it.

```bash
cd video
npm install
npm run render -- reels/example.json      # -> out/example.mp4
npm run studio                            # live preview in the browser (local machine)
```

Edit or copy `reels/example.json` to make a new video. In Claude Code, the
`/reel-video` skill writes the JSON for you from an `/ig-reel` script and
renders it.

Remotion is free for individuals and companies of up to 3 people; larger
companies need a license (https://www.remotion.dev/license).
