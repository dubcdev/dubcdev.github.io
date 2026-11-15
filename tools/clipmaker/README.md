# Snake Parade clip maker

Makes 1080x1920 vertical clips from the real game (no people, gameplay only).

1. Copy the game's `www/` to a scratch folder `W`, add fonts (`npm pack @fontsource/lilita-one @fontsource/nunito`, latin woff2 into `www/fonts/` as lilita.woff2 and nunito-400/700/800/900.woff2, point index.html's @font-face rules at them) and expose hooks: add `window.__t={G,S,genTo,getRows:()=>rows,turn,hopForward,beginRun,prepRun};` just before the final `})();` of `www/js/game.js`. Never commit these changes to the game repo.
2. Serve `W/www` on 127.0.0.1:8765 and run `python3 rec.py scenes.json` (Playwright + /usr/bin/google-chrome). Each scene picks a snake (`char`), places critters at (dx, dr) from the head, clears hazards up to the nest and steers the snake to pick them up one at a time and deliver them home.
3. `python3 finish.py hooks.json` adds the 2-line hook pills and the 2.5 s end card.
4. Add music: for each clip, `python3 music.py <duration> music.wav` renders the game's own theme (same notes as the Music synth in game.js) and ffmpeg muxes it in with `loudnorm=I=-16:TP=-1.5:LRA=11`.
5. Look at sample frames of every clip before using it.

Paths in the scripts assume `/tmp/claude-0/clipwork` as `W`; edit BASE/OUT if different.
