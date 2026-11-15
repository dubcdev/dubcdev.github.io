import json, subprocess, sys
from PIL import Image, ImageDraw, ImageFont

W, H = 1080, 1920
BASE = '/tmp/claude-0/clipwork'
LIL = f'{BASE}/www/fonts/lilita.woff2'
# Pillow can't read woff2; convert once with fonttools if needed
import os
TTF = f'{BASE}/lilita.ttf'
if not os.path.exists(TTF):
    from fontTools.ttLib import TTFont
    f = TTFont(LIL); f.flavor = None; f.save(TTF)
NUN = f'{BASE}/nunito900.ttf'
if not os.path.exists(NUN):
    from fontTools.ttLib import TTFont
    f = TTFont(f'{BASE}/www/fonts/nunito-900.woff2'); f.flavor = None; f.save(NUN)

def hook_png(lines, path):
    im = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    y = 235
    for i, txt in enumerate(lines):
        size = 82 if i == 0 else 64
        font = ImageFont.truetype(TTF, size)
        bb = d.textbbox((0, 0), txt, font=font)
        tw, th = bb[2] - bb[0], bb[3] - bb[1]
        padx, pady = 40, 26
        x0 = (W - tw) // 2 - padx
        box = [x0, y, x0 + tw + 2 * padx, y + th + 2 * pady]
        d.rounded_rectangle([box[0] + 6, box[1] + 8, box[2] + 6, box[3] + 8], radius=46, fill=(29, 36, 51, 140))
        d.rounded_rectangle(box, radius=46, fill=(255, 255, 255, 245) if i == 0 else (255, 154, 77, 250))
        d.text(((W - tw) // 2 - bb[0], y + pady - bb[1]), txt, font=font, fill=(29, 36, 51) if i == 0 else (255, 255, 255))
        y = box[3] + 18
    im.save(path)

def endcard_png(path):
    im = Image.new('RGB', (W, H))
    d = ImageDraw.Draw(im)
    for yy in range(H):
        t = yy / H
        c = (int(255 - 20 * t), int(170 - 70 * t), int(80 - 40 * t))
        d.line([(0, yy), (W, yy)], fill=c)
    icon = Image.open('/home/claude/snake-parade/assets/icon-1024.png').convert('RGBA').resize((420, 420), Image.LANCZOS)
    mask = Image.new('L', (420, 420), 0); ImageDraw.Draw(mask).rounded_rectangle([0, 0, 419, 419], radius=92, fill=255)
    im.paste(icon, ((W - 420) // 2, 470), mask)
    def center(txt, font, y, fill):
        bb = d.textbbox((0, 0), txt, font=font)
        d.text(((W - (bb[2] - bb[0])) // 2 - bb[0], y), txt, font=font, fill=fill)
    center('Snake Parade™', ImageFont.truetype(TTF, 120), 960, (255, 255, 255))
    center('Free on iPhone', ImageFont.truetype(TTF, 84), 1120, (29, 36, 51))
    center('Search "Snake Parade" on the App Store', ImageFont.truetype(NUN, 44), 1250, (255, 255, 255))
    im.save(path)

def build(name, lines, out):
    hook_png(lines, f'{BASE}/raw/{name}_hook.png')
    endcard_png(f'{BASE}/raw/endcard.png')
    dur = float(subprocess.check_output(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', f'{BASE}/raw/{name}.mp4']))
    fc = ('[0:v][1:v]overlay=0:0:enable=\'lt(t,%.2f)\'[g];' % (dur - 0.2) +
          '[2:v]scale=1080:1920,format=yuv420p,setsar=1[e];'
          '[g]format=yuv420p,setsar=1[g2];[g2][e]concat=n=2:v=1:a=0,fps=30[v]')
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', f'{BASE}/raw/{name}.mp4', '-i', f'{BASE}/raw/{name}_hook.png',
                    '-loop', '1', '-t', '2.5', '-i', f'{BASE}/raw/endcard.png',
                    '-f', 'lavfi', '-t', str(dur + 2.5), '-i', 'anullsrc=r=44100:cl=stereo',
                    '-filter_complex', fc, '-map', '[v]', '-map', '3:a', '-shortest',
                    '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '20', '-c:a', 'aac', '-movflags', '+faststart', out], check=True)
    print(out)

if __name__ == '__main__':
    hooks = json.load(open(sys.argv[1]))
    os.makedirs(f'{BASE}/final', exist_ok=True)
    for name, v in hooks.items():
        build(name, v['lines'], f"{BASE}/final/{v['file']}")
