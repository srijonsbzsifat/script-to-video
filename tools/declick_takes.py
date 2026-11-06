#!/usr/bin/env python3
"""Remove the noise burst Gemini TTS leaves at the end of every take (about 0.15 s of broadband hiss at about -12 dB,
then digital silence, then a blip at the start of the next take). Timing is unchanged: the bursts are muted, not cut.

  declick_takes.py IN_AUDIO OUT.wav
"""
import subprocess, sys
import numpy as np

SR = 48000
HOP = SR // 100                                                  # 10 ms frames


def main(src, dst):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", src, "-f", "f32le", "-ac", "2", "-ar", str(SR), "-"], capture_output=True, check=True).stdout
    x = np.frombuffer(raw, np.float32).reshape(-1, 2).copy()
    n = len(x) // HOP
    fr = x[: n * HOP].reshape(n, HOP, 2).mean(2)
    rms = 20 * np.log10(np.sqrt((fr ** 2).mean(1)) + 1e-9)
    zero = rms < -120                                         # (a frame that is mostly digital zero)
    cen = np.array([(np.abs(np.fft.rfft(f * np.hanning(HOP))) * np.fft.rfftfreq(HOP, 1 / SR)).sum() / (np.abs(np.fft.rfft(f * np.hanning(HOP))).sum() + 1e-9) for f in fr])
    i = 0
    while i < n:
        if not zero[i]: i += 1; continue
        j = i
        while j < n and zero[j]: j += 1
        if j - i >= 5:                                           # a gap of 50 ms or more of digital zero = a take join or the end
            a = i
            while i - a < 2 and rms[a - 1] <= -62: a -= 1          # a frame that is only partly zero
            a0 = a
            while a > 0 and a0 - a < 25 and rms[a - 1] > -62 and cen[a - 1] > 3000: a -= 1     # the hiss before it
            if a == a0: a = i
            b = min(n, j + 5)
            while b < n and rms[b] < -45: b += 1                  # blips and room noise until speech starts again
            print(f"muted {a * 0.01:.2f} to {b * 0.01:.2f} s")
            x[a * HOP: b * HOP] = 0
        i = j
    sys.stdout.flush()
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "f32le", "-ac", "2", "-ar", str(SR), "-i", "-", dst], input=x.tobytes(), check=True)


if __name__ == "__main__":
    if len(sys.argv) != 3: sys.exit(__doc__)
    main(sys.argv[1], sys.argv[2])
