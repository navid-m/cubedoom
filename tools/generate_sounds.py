#!/usr/bin/env python3
"""Generate the small WAV sound set used by cubedoom."""

import math
import random
import struct
import wave
from pathlib import Path

RATE = 44100
OUT = Path(__file__).resolve().parent.parent / "sounds"


def write_wav(name, samples):
    OUT.mkdir(exist_ok=True)
    peak = max(1.0, max(abs(s) for s in samples))
    data = bytearray()
    for s in samples:
        v = int(max(-1.0, min(1.0, s / peak)) * 30000)
        data += struct.pack("<h", v)
    with wave.open(str(OUT / name), "wb") as f:
        f.setnchannels(1)
        f.setsampwidth(2)
        f.setframerate(RATE)
        f.writeframes(bytes(data))


def envelope(i, n, attack=0.01, release=0.2):
    a = max(1, int(n * attack))
    r = max(1, int(n * release))
    if i < a:
        return i / a
    if i > n - r:
        return max(0.0, (n - i) / r)
    return 1.0


def tone(n, freq_start, freq_end=None, noise=0.0, wobble=0.0, seed=1):
    rng = random.Random(seed)
    out = []
    phase = 0.0
    for i in range(n):
        t = i / n
        f = freq_start if freq_end is None else freq_start + (freq_end - freq_start) * t
        f *= 1.0 + wobble * math.sin(t * math.pi * 9.0)
        phase += 2.0 * math.pi * f / RATE
        s = math.sin(phase)
        if noise:
            s = s * (1.0 - noise) + rng.uniform(-1.0, 1.0) * noise
        out.append(s * envelope(i, n))
    return out


def main():
    write_wav("shoot.wav", tone(int(RATE * 0.18), 170.0, 42.0, 0.48, 0.4, 1))
    write_wav("enemy_shoot.wav", tone(int(RATE * 0.22), 95.0, 38.0, 0.30, 0.2, 2))
    write_wav("hit.wav", tone(int(RATE * 0.10), 420.0, 110.0, 0.55, 0.8, 3))
    write_wav("hurt.wav", tone(int(RATE * 0.30), 120.0, 55.0, 0.22, 0.6, 4))
    write_wav("pickup.wav", tone(int(RATE * 0.34), 520.0, 1040.0, 0.02, 0.0, 5))
    write_wav("footstep.wav", tone(int(RATE * 0.09), 70.0, 45.0, 0.65, 0.0, 6))
    print("wrote sounds to", OUT)


if __name__ == "__main__":
    main()
