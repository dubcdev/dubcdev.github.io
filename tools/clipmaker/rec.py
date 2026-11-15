import asyncio, base64, json, os, sys, subprocess, time
from playwright.async_api import async_playwright

URL = 'http://127.0.0.1:8765/index.html'
OUT = '/tmp/claude-0/clipwork/raw'

SCENE_JS = r"""
async (cfg) => {
  const sleep = ms => new Promise(r => setTimeout(r, ms));
  const t = window.__t, G = t.G;
  t.prepRun(); t.beginRun();
  await sleep(300);
  const rows = t.getRows();
  const head = G.snake[0];
  t.genTo(head.r + 70);
  let nest = null;
  for (let r = head.r + cfg.nestMin; r < head.r + 70; r++) if (rows[r] && rows[r].lane === 'nest') { nest = r; break; }
  if (nest === null) return {err: 'no nest'};
  for (let r = head.r - 2; r < nest; r++) {
    const row = rows[r]; if (!row) continue;
    if (row.lane && row.lane !== 'nest') row.lane = null;
    row.rollers = null; row.pads = null; row.power = null; row.sticker = null; row.critters = [];
    for (let c = 0; c < row.cells.length; c++) row.cells[c] = 0;
  }
  for (let r = nest; r < nest + 6; r++) if (rows[r]) { rows[r].sticker = null; rows[r].power = null; }
  const W = 12, wrap = x => ((x % W) + W) % W;
  const targets = cfg.critters.map((c, i) => ({ r: head.r + c.dr, c: wrap(head.x + c.dx), type: c.type }));
  for (const tg of targets) rows[tg.r].critters.push({ c: tg.c, type: tg.type, wob: Math.random() * 6 });
  window.__recStart = true;
  await sleep(cfg.lead || 700);
  const hop = async (dx, dy) => { G.idle = 0; t.turn(dx, dy); await sleep(cfg.ms || 390); };
  let x = head.x, r = head.r;
  for (const tg of targets) {
    while (r < tg.r - 1) { await hop(0, 1); r++; }
    let d = tg.c - x; if (d > 6) d -= 12; if (d < -6) d += 12;
    while (d !== 0) { const s = Math.sign(d); await hop(s, 0); x = wrap(x + s); d -= s; }
    await hop(0, 1); r++;
  }
  while (r < nest) { await hop(0, 1); r++; }
  await sleep(cfg.tail || 1600);
  return {ok: true, nest, start: head.r, rescued: G.rescued};
}
"""

async def record(name, cfg):
    os.makedirs(f'{OUT}/{name}', exist_ok=True)
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path='/usr/bin/google-chrome', args=['--autoplay-policy=no-user-gesture-required'])
        ctx = await b.new_context(viewport={'width': 920, 'height': 1636})
        seed = cfg.get('seed', 7)
        await ctx.add_init_script("""
          (() => { let s = %d >>> 0; Math.random = () => { s = (s * 1664525 + 1013904223) >>> 0; return s / 4294967296; };
          const set = (k, v) => localStorage.setItem('slither:' + k, JSON.stringify(v));
          set('tutDone', true); set('ageGroup', 'adult'); set('muted', true); set('sfx', false); set('music', false);
          set('runs', 12); set('char', %s); set('owned', %s); set('seenPow', {magnet:1,nap:1,shield:1,ghost:1}); set('tips', {all:1}); set('giftDay', new Date().toDateString()); })();
        """ % (seed, json.dumps(cfg['char']), json.dumps(cfg.get('owned', ['cowboy', cfg['char']]))))
        page = await ctx.new_page()
        await page.goto(URL)
        await page.add_style_tag(content='#coach,#toast{display:none!important} html{zoom:2}')
        await page.wait_for_timeout(1500)
        cdp = await ctx.new_cdp_session(page)
        frames = []
        recording = {'on': False}
        async def on_frame(ev):
            if recording['on']:
                frames.append((ev['metadata']['timestamp'], ev['data']))
            await cdp.send('Page.screencastFrameAck', {'sessionId': ev['sessionId']})
        cdp.on('Page.screencastFrame', lambda ev: asyncio.ensure_future(on_frame(ev)))
        await cdp.send('Page.startScreencast', {'format': 'jpeg', 'quality': 92, 'everyNthFrame': 1, 'maxWidth': 920, 'maxHeight': 1636})
        task = asyncio.ensure_future(page.evaluate(SCENE_JS, cfg))
        while not await page.evaluate('!!window.__recStart'):
            await asyncio.sleep(0.02)
        recording['on'] = True
        res = await task
        recording['on'] = False
        await cdp.send('Page.stopScreencast')
        await b.close()
    lst = []
    for i, (ts, data) in enumerate(frames):
        fn = f'{OUT}/{name}/f{i:05d}.jpg'
        open(fn, 'wb').write(base64.b64decode(data))
        dur = (frames[i + 1][0] - ts) if i + 1 < len(frames) else 0.04
        lst.append(f"file '{fn}'\nduration {max(dur, 0.001):.4f}")
    lst.append(f"file '{OUT}/{name}/f{len(frames)-1:05d}.jpg'")
    open(f'{OUT}/{name}/list.txt', 'w').write('\n'.join(lst))
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'concat', '-safe', '0', '-i', f'{OUT}/{name}/list.txt',
                    '-vf', 'scale=1080:1920:flags=lanczos,fps=30,format=yuv420p', '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '18',
                    f'{OUT}/{name}.mp4'], check=True)
    print(name, res, len(frames), 'frames')

if __name__ == '__main__':
    cfgs = json.load(open(sys.argv[1]))
    only = sys.argv[2:]
    for name, cfg in cfgs.items():
        if only and name not in only: continue
        asyncio.run(record(name, cfg))
