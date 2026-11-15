# Renders Snake Parade's in-game theme (the Music synth in www/js/game.js) to a WAV, note for note.
import numpy as np, wave, sys
SR = 44100
BPM = 116; STEP = 60 / BPM / 2
MEL = [659, 0, 523, 0, 392, 523, 659, 784, 440, 0, 523, 0, 659, 587, 523, 0, 587, 0, 392, 440, 587, 0, 784, 0, 659, 587, 523, 392, 523, 0, 0, 0,
       784, 0, 659, 0, 523, 0, 659, 784, 880, 0, 784, 659, 523, 0, 440, 0, 784, 0, 659, 587, 587, 0, 392, 0, 523, 0, 392, 0, 523, 0, 0, 0]
BASS = [131, 196, 131, 196, 175, 262, 175, 262, 196, 294, 196, 294, 131, 196, 131, 196]

def osc(kind, f, n):
    t = np.arange(n) / SR; ph = (f * t) % 1
    if kind == 'square': return np.where(ph < .5, 1.0, -1.0)
    return 4 * np.abs(ph - .5) - 1  # triangle

def env(n, vol, d):
    t = np.arange(n) / SR; e = np.empty(n)
    a = t < .012
    e[a] = .0001 * (vol / .0001) ** (t[a] / .012)
    b = ~a
    e[b] = vol * (.0001 / vol) ** np.clip((t[b] - .012) / max(d - .012, 1e-3), 0, 1)
    return e

def note(buf, f, t0, d, kind, vol):
    n = int((d + .03) * SR); i = int(t0 * SR)
    if i >= len(buf): return
    n = min(n, len(buf) - i)
    buf[i:i + n] += osc(kind, f, n) * env(n, vol, d)

def render(seconds, start_step=0):
    buf = np.zeros(int(seconds * SR) + SR)
    t, step = 0.05, start_step
    while t < seconds:
        m = MEL[step % len(MEL)]
        if m: note(buf, m, t, STEP * .85, 'square', .05)
        if step % 2 == 0:
            b = BASS[(step >> 1) % len(BASS)]
            if b: note(buf, b, t, STEP * 1.7, 'triangle', .14)
        if step % 4 == 2: note(buf, 2200, t, .025, 'square', .018)
        t += STEP; step += 1
    buf = buf[:int(seconds * SR)] * .32
    return buf

if __name__ == '__main__':
    secs = float(sys.argv[1]); out = sys.argv[2]; start = int(sys.argv[3]) if len(sys.argv) > 3 else 0
    x = render(secs, start)
    x = x / max(1e-9, np.abs(x).max()) * .8
    fade = int(1.5 * SR); x[-fade:] *= np.linspace(1, 0, fade)
    pcm = (x * 32767).astype(np.int16)
    st = np.repeat(pcm[:, None], 2, axis=1)
    with wave.open(out, 'wb') as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(st.tobytes())
    print(out, secs)
