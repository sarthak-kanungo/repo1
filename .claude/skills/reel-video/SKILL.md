---
name: reel-video
description: Render an Instagram Reel or LinkedIn video as an MP4 from on-screen text, using the Remotion project in video/. Use when the user says "make the video", "render this reel", "turn this script into a video", or has an /ig-reel beat sheet and wants the actual file. Animated kinetic text only - no footage, no AI-generated people.
---

# reel-video

Turns a script into a 1080x1920 vertical MP4 with animated on-screen text, a
progress bar and the user's handle. The project lives in `video/` at the repo
root.

## Steps

1. **Get the script.** If the user has not run `/ig-reel` yet and only has an
   idea, run `/ig-reel` first. The beat sheet's on-screen text is the input.
2. **Write the scene file** at `video/reels/<short-name>.json`, same shape as
   `video/reels/example.json`:
   - `scenes`: one entry per beat. `text` is the on-screen line (3-8 words
     reads at a glance), `sub` is an optional smaller line, `seconds` is how
     long it stays up. Scene 1 is the hook and renders larger.
   - Wrap the one or two words that matter in `*asterisks*` to colour them.
     Use it on numbers and the payoff, not on every scene.
   - `handle`: the user's @handle. Ask once if you do not know it.
   - `theme`: optional `background`, `text`, `accent` hex colours.
   - Keep the total between 7 and 30 seconds unless the user asks otherwise.
   Run the text through `/ig-human` first. Never put invented numbers or
   claims on screen.
3. **Render:** from `video/`, run `npm install` if `node_modules` is missing,
   then `npm run render -- reels/<short-name>.json`. Output goes to
   `video/out/<short-name>.mp4`.
4. **Check it:** pull a few frames with ffmpeg (for example
   `ffmpeg -i out/<name>.mp4 -vf "select='eq(n\,30)+eq(n\,150)',scale=270:-1,tile=2x1" -frames:v 1 -fps_mode vfr frames.png`)
   and look at them for overflowing or clipped text before handing it over.
5. **Hand over the file** and remind the user they post it themselves. This
   skill never uploads anything.

Out of scope here: voiceover, music, stock footage. The user adds audio in
Instagram's editor or CapCut after export.
