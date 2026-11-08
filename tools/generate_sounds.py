#!/usr/bin/env python3
"""Generate the WAV sound set used by cubedoom.

Every effect in sounds/ (apart from hup.wav, which is supplied) is produced
here, so the audio can be regenerated without any sample assets.
"""

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


def decay_env(i, n, curve=5.0):
    return math.exp(-curve * (i / max(1, n)))


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


def thump(duration, f0, f1, noise_amt, seed, curve=6.0):
    n = int(RATE * duration)
    rng = random.Random(seed)
    out = []
    phase = 0.0
    low = 0.0
    for i in range(n):
        t = i / n
        f = f0 + (f1 - f0) * (t ** 0.55)
        phase += 2.0 * math.pi * f / RATE
        low += (rng.uniform(-1.0, 1.0) - low) * 0.18
        s = math.sin(phase) * 0.70 + low * noise_amt
        out.append(s * decay_env(i, n, curve))
    return out


def noise_burst(duration, amount, seed, curve=9.0, smooth=0.30):
    n = int(RATE * duration)
    rng = random.Random(seed)
    out = []
    state = 0.0
    for i in range(n):
        state += (rng.uniform(-1.0, 1.0) - state) * smooth
        out.append(state * amount * decay_env(i, n, curve))
    return out


def mix(*tracks):
    n = max(len(t) for t in tracks)
    out = [0.0] * n
    for track in tracks:
        for i, v in enumerate(track):
            out[i] += v
    return out


def delayed(track, delay, gain=1.0):
    offset = int(RATE * delay)
    out = [0.0] * (len(track) + offset)
    for i, v in enumerate(track):
        out[i + offset] += v * gain
    return out


def arpeggio(notes, step, decay):
    n = int(RATE * step * len(notes))
    out = [0.0] * n
    for note_index, freq in enumerate(notes):
        start = int(RATE * step * note_index)
        length = int(RATE * step * 2.4)
        for i in range(length):
            if start + i >= n:
                break
            t = i / length
            phase = 2.0 * math.pi * freq * (i / RATE)
            out[start + i] += (math.sin(phase) + 0.25 * math.sin(phase * 2.0)) * decay_env(
                i, length, decay
            )
    return out


def main():
    # Legacy/core sounds.
    write_wav("shoot.wav", thump(0.18, 170.0, 42.0, 0.55, 1, 7.0))
    write_wav("enemy_shoot.wav", thump(0.22, 95.0, 38.0, 0.35, 2, 5.0))
    write_wav("hit.wav", mix(noise_burst(0.10, 0.7, 3, 12.0), tone(int(RATE * 0.10), 420.0, 110.0, 0.55, 0.8, 3)))
    write_wav("hurt.wav", thump(0.30, 120.0, 55.0, 0.30, 4, 3.2))
    write_wav("pickup.wav", tone(int(RATE * 0.34), 520.0, 1040.0, 0.02, 0.0, 5))
    write_wav("footstep.wav", tone(int(RATE * 0.09), 70.0, 45.0, 0.65, 0.0, 6))

    # Weapon fire sounds.
    write_wav(
        "shoot_machinegun.wav",
        mix(
            thump(0.085, 240.0, 65.0, 0.80, 11, 11.0),
            noise_burst(0.070, 0.85, 12, 14.0, 0.55),
            delayed(noise_burst(0.050, 0.35, 13, 18.0, 0.40), 0.045),
        ),
    )
    write_wav(
        "shoot_shotgun.wav",
        mix(
            thump(0.36, 130.0, 32.0, 0.85, 21, 4.6),
            noise_burst(0.34, 0.95, 22, 4.2, 0.16),
            delayed(thump(0.24, 170.0, 45.0, 0.65, 23, 6.0), 0.055, 0.85),
            delayed(noise_burst(0.20, 0.55, 24, 6.5, 0.22), 0.060, 0.80),
        ),
    )
    write_wav(
        "shoot_plasma.wav",
        mix(
            tone(int(RATE * 0.24), 1400.0, 210.0, 0.06, 0.42, 31),
            tone(int(RATE * 0.24), 700.0, 110.0, 0.03, 0.28, 32),
            noise_burst(0.12, 0.22, 33, 8.0, 0.70),
        ),
    )

    # Weapon switch / equip sounds.
    write_wav(
        "weapon_machinegun.wav",
        mix(
            noise_burst(0.10, 0.42, 41, 15.0, 0.72),
            tone(int(RATE * 0.16), 620.0, 280.0, 0.10, 0.12, 42),
            delayed(noise_burst(0.085, 0.30, 43, 15.0, 0.60), 0.080),
        ),
    )
    write_wav(
        "weapon_shotgun.wav",
        mix(
            thump(0.25, 220.0, 90.0, 0.55, 51, 8.0),
            noise_burst(0.18, 0.55, 52, 9.0, 0.52),
            delayed(noise_burst(0.16, 0.48, 53, 10.0, 0.45), 0.105, 1.0),
        ),
    )
    write_wav(
        "weapon_plasma.wav",
        mix(
            tone(int(RATE * 0.30), 280.0, 1500.0, 0.03, 0.30, 61),
            tone(int(RATE * 0.30), 140.0, 750.0, 0.02, 0.16, 62),
            noise_burst(0.20, 0.12, 63, 5.5, 0.75),
        ),
    )

    # Shotgun reload animation clicks.
    write_wav(
        "reload_shotgun_1.wav",
        mix(noise_burst(0.10, 0.55, 71, 16.0, 0.60), thump(0.09, 520.0, 220.0, 0.20, 72, 13.0)),
    )
    write_wav(
        "reload_shotgun_2.wav",
        mix(noise_burst(0.12, 0.60, 73, 14.0, 0.52), thump(0.12, 360.0, 150.0, 0.32, 74, 11.0)),
    )

    # Pickups, shop, wave, and UI.
    write_wav(
        "xp.wav",
        mix(
            tone(int(RATE * 0.18), 1046.0, 1568.0, 0.0, 0.0, 81),
            delayed(tone(int(RATE * 0.18), 1568.0, 2093.0, 0.0, 0.0, 82), 0.055, 0.75),
            delayed(tone(int(RATE * 0.14), 2093.0, 2637.0, 0.0, 0.0, 83), 0.110, 0.45),
        ),
    )
    write_wav("buy.wav", arpeggio([523.25, 659.25, 783.99, 1046.50], 0.075, 4.5))
    write_wav("click.wav", mix(noise_burst(0.045, 0.40, 91, 22.0, 0.65), tone(int(RATE * 0.055), 900.0, 520.0, 0.05, 0.0, 92)))
    write_wav(
        "wave_start.wav",
        mix(
            tone(int(RATE * 0.65), 82.0, 61.0, 0.02, 0.0, 101),
            tone(int(RATE * 0.65), 164.0, 122.0, 0.01, 0.0, 102),
            delayed(noise_burst(0.30, 0.18, 103, 3.5, 0.08), 0.08),
        ),
    )
    write_wav(
        "death.wav",
        mix(
            thump(0.85, 110.0, 28.0, 0.45, 111, 2.4),
            tone(int(RATE * 0.85), 220.0, 55.0, 0.08, 0.5, 112),
        ),
    )

    print("wrote sounds to", OUT)


if __name__ == "__main__":
    main()
