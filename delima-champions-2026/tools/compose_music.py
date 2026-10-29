"""Gubah muzik latar asal 60 s, 125 BPM, D major -> tools/out/music.mid

Struktur (1 bar = 1.92 s):
  bar 0-2   intro: strings membina, arp masuk, roll timpani      (0.00-5.76)
  bar 3-6   tema A penuh: dram masuk serentak logo DELIMa         (5.76-13.44)
  bar 7-14  groove ringan di bawah narasi                          (13.44-28.80)
  bar 15-22 seksyen B (progresi lain)                              (28.80-44.16)
  bar 23-26 build ke Grand Lucky Draw, snare roll bar 26           (44.16-51.84)
  bar 27-29 finale tema A                                          (51.84-57.60)
  bar 30    kord penamat + loceng, reda ke 60 s                    (57.60-60.00)

Render: node tools/render_music.mjs   (-> assets/audio/stems/music.wav)
"""
import os
import mido

BPM = 125
TPB = 480  # ticks per beat
BAR = 4 * TPB
OUT = os.path.join(os.path.dirname(__file__), "out")

# chord = (root midi note in bass octave, chord tones as pitch classes offsets)
D, E, Fs, G, A, B, Cs = 50, 52, 54, 55, 57, 59, 49
MAJ, MIN = (0, 4, 7), (0, 3, 7)
CH = {
    "D": (D, MAJ), "A": (A - 12, MAJ), "Bm": (B - 12, MIN), "G": (G - 12, MAJ),
    "Em": (E, MIN), "F#m": (Fs - 12, MIN), "Asus": (A - 12, (0, 5, 7)),
}

# one chord per bar, 31 bars (+ final)
PROG = (
    ["D", "D", "Asus"]                      # intro 0-2
    + ["D", "A", "Bm", "G"]                 # theme A 3-6
    + ["D", "G", "Bm", "A", "D", "G", "Em", "A"]   # groove 7-14
    + ["G", "A", "F#m", "Bm", "G", "A", "D", "D"]  # B 15-22
    + ["Em", "G", "A", "A"]                 # build 23-26
    + ["D", "A", "Bm"]                      # finale 27-29
    + ["D", "D"]                            # end 30-31
)

# channels
STR, PAD, BRASS, LEAD, ARP, BASS, TIMP, BELL, HIT = range(9)
DRUM = 9
PROGRAMS = {STR: 48, PAD: 89, BRASS: 61, LEAD: 81, ARP: 81, BASS: 38, TIMP: 47, BELL: 9, HIT: 55}

events = []  # (tick, order, msg)


def note(ch, n, start, dur, vel):
    events.append((int(start), 1, mido.Message("note_on", channel=ch, note=n, velocity=max(1, min(127, int(vel))))))
    events.append((int(start + dur) - 1, 0, mido.Message("note_off", channel=ch, note=n, velocity=0)))


def cc(ch, ctrl, val, t):
    events.append((int(t), 0, mido.Message("control_change", channel=ch, control=ctrl, value=int(max(0, min(127, val))))))


def tones(name, octave_from):
    root, iv = CH[name]
    pcs = [(root + i) % 12 for i in iv]
    out = []
    for n in range(octave_from, octave_from + 30):
        if n % 12 in pcs:
            out.append(n)
    return out


# ---------- setup ----------
for ch, p in PROGRAMS.items():
    events.append((0, 0, mido.Message("program_change", channel=ch, program=p)))
    cc(ch, 91, 50, 0)  # reverb
    cc(ch, 93, 10, 0)  # chorus
mix = {STR: 92, PAD: 60, BRASS: 96, LEAD: 70, ARP: 58, BASS: 96, TIMP: 100, BELL: 80, HIT: 90}
pan = {STR: 52, PAD: 64, BRASS: 70, LEAD: 58, ARP: 40, BASS: 64, TIMP: 64, BELL: 84, HIT: 64}
for ch in mix:
    cc(ch, 7, mix[ch], 0)
    cc(ch, 10, pan[ch], 0)
cc(ARP, 74, 70, 0)
cc(DRUM, 7, 100, 0)
cc(DRUM, 91, 30, 0)


def section(bar):
    if bar <= 2:
        return "intro"
    if bar <= 6:
        return "A"
    if bar <= 14:
        return "groove"
    if bar <= 22:
        return "B"
    if bar <= 26:
        return "build"
    if bar <= 29:
        return "finale"
    return "end"


# ---------- strings + pad: sustained chords ----------
for bar, name in enumerate(PROG):
    t = bar * BAR
    sec = section(bar)
    if bar == 31:
        break
    voicing = [n for n in tones(name, 62) if n <= 76][:4]
    if sec == "end":
        voicing = [62, 66, 69, 74, 78]
        note(STR, 50, t, BAR * 1.25, 100)
        for n in voicing:
            note(STR, n, t, BAR * 1.25, 100)
            note(PAD, n, t, BAR * 1.25, 70)
        break
    vel = {"intro": 70 + bar * 12, "A": 96, "groove": 72, "B": 80, "build": 84 + (bar - 23) * 8, "finale": 104}[sec]
    for n in voicing:
        note(STR, n, t, BAR, vel)
        note(PAD, n - 12, t, BAR, 64)

# intro swell on strings (expression)
for i in range(0, 3 * 16):
    cc(STR, 11, 40 + i * 1.8, i * TPB / 4)
cc(STR, 11, 127, 3 * BAR)
# soften strings under narration
for bar in range(7, 23):
    cc(STR, 11, 100, bar * BAR)
cc(STR, 11, 127, 23 * BAR)

# ---------- arp: 16ths over chord tones ----------
for bar, name in enumerate(PROG[:30]):
    sec = section(bar)
    if bar == 0:
        continue
    pool = [n for n in tones(name, 62) if n <= 86][:7]
    pattern = [0, 2, 4, 1, 3, 5, 2, 6, 4, 2, 5, 3, 1, 4, 2, 0]
    for s in range(16):
        n = pool[pattern[s] % len(pool)]
        acc = 1.0 if s % 4 == 0 else 0.78
        base = {"intro": 40 + bar * 14, "A": 78, "groove": 64, "B": 70, "build": 72 + (bar - 23) * 6, "finale": 84}[sec]
        note(ARP, n, bar * BAR + s * TPB / 4, TPB / 4 * 0.85, base * acc)
    # filter opens through the intro
    if sec == "intro":
        for s in range(16):
            cc(ARP, 74, 40 + (bar - 1) * 40 + s * 2.5, bar * BAR + s * TPB / 4)
    elif bar == 3:
        cc(ARP, 74, 90, bar * BAR)

# ---------- bass: driving 8ths ----------
for bar, name in enumerate(PROG[:31]):
    sec = section(bar)
    root = CH[name][0] - 12  # octave 2
    if sec == "intro":
        if bar == 2:
            note(BASS, root, bar * BAR + 2 * TPB, 2 * TPB, 80)
        continue
    if sec == "end":
        note(BASS, 38, bar * BAR, BAR * 1.2, 110)
        break
    for e in range(8):
        vel = 104 if e % 2 == 0 else 84
        if sec == "groove":
            vel -= 10
        n = root + (12 if e in (3, 7) and sec in ("A", "finale") else 0)
        note(BASS, n, bar * BAR + e * TPB / 2, TPB / 2 * 0.8, vel)

# ---------- melody: brass (mid) + synth lead (high) ----------
# (beat offset, semitone above D4=62, length in beats)
THEME = [
    # bar 1 (D)
    [(0, 0, 1), (1, 4, 0.5), (1.5, 7, 0.5), (2, 12, 1.5), (3.5, 11, 0.5)],
    # bar 2 (A)
    [(0, 9, 0.5), (0.5, 7, 0.5), (1, 2, 1), (2, 7, 2)],
    # bar 3 (Bm)
    [(0, 9, 1), (1, 12, 0.5), (1.5, 11, 0.5), (2, 9, 1), (3, 4, 1)],
    # bar 4 (G)
    [(0, 5, 1), (1, 7, 0.5), (1.5, 9, 0.5), (2, 7, 2)],
]
THEME_END = [(0, 5, 1), (1, 7, 0.5), (1.5, 9, 0.5), (2, 11, 2)]  # G -> leads to D


def play_theme(bar0, brass_vel, lead_vel, ending=False, bars=4):
    for i in range(bars):
        phrase = THEME_END if (ending and i == 3) else THEME[i]
        for off, semi, ln in phrase:
            t = (bar0 + i) * BAR + off * TPB
            note(BRASS, 62 + semi - 12, t, ln * TPB * 0.95, brass_vel)
            note(BRASS, 62 + semi, t, ln * TPB * 0.95, brass_vel - 10)
            note(LEAD, 62 + semi + 12, t, ln * TPB * 0.9, lead_vel)


play_theme(3, 104, 78)
# finale: three bars of the theme then the final chord
play_theme(27, 116, 86, bars=3)

# groove: sparse lead answers between narration (bar 2 & 4 of each 4)
for bar0 in (8, 12):
    for off, semi, ln in [(2, 12, 0.5), (2.5, 11, 0.5), (3, 9, 1)]:
        note(LEAD, 62 + semi + 12, bar0 * BAR + off * TPB, ln * TPB * 0.9, 58)
# B section: brass pads on the downbeats
for bar in range(15, 23):
    name = PROG[bar]
    for n in [x for x in tones(name, 55) if x <= 67][:3]:
        note(BRASS, n, bar * BAR, TPB * 1.5, 74)
        note(BRASS, n, bar * BAR + 2.5 * TPB, TPB * 1.0, 66)
# build: rising brass stabs
for bar in range(23, 27):
    name = PROG[bar]
    for b in range(4):
        for n in [x for x in tones(name, 57) if x <= 70][:3]:
            note(BRASS, n, bar * BAR + b * TPB, TPB * 0.4, 70 + (bar - 23) * 10 + b * 2)
# final chord: brass + hit + timpani + bells
FINAL = 30 * BAR
for n in (50, 57, 62, 66, 69, 74):
    note(BRASS, n, FINAL, BAR * 1.1, 112)
note(HIT, 62, FINAL, TPB * 2, 110)
note(HIT, 74, FINAL, TPB * 2, 100)
for i, n in enumerate((86, 90, 93, 98)):
    note(BELL, n, FINAL + i * TPB / 4, TPB * 3, 92 - i * 6)

# ---------- timpani & orchestra hits ----------
# intro roll bar 2 (crescendo) -> hit on bar 3 with the DELIMa logo
for s in range(32):
    note(TIMP, 45 if s % 2 else 45, 2 * BAR + s * TPB / 8, TPB / 8, 50 + s * 2.2)
note(TIMP, 38, 3 * BAR, TPB * 2, 120)
note(HIT, 62, 3 * BAR, TPB * 2, 104)
for bar in (7, 15, 23, 27):
    note(TIMP, 38, bar * BAR, TPB * 1.5, 96)
note(HIT, 62, 27 * BAR, TPB * 2, 100)

# ---------- drums ----------
KICK, SNARE, CLAP, HAT, OHAT, CRASH, RIDE, TOM_L, TOM_M, TOM_H = 36, 38, 39, 42, 46, 49, 51, 45, 47, 50


def d(n, t, vel):
    note(DRUM, n, t, TPB / 4, vel)


for bar in range(31):
    sec = section(bar)
    t0 = bar * BAR
    if sec == "intro":
        if bar == 2:
            for s in range(8, 16):  # snare build, last half bar
                d(SNARE, t0 + s * TPB / 4, 40 + (s - 8) * 9)
        continue
    if sec == "end":
        d(CRASH, t0, 118)
        d(KICK, t0, 120)
        break
    crash_bars = (3, 7, 15, 23, 27)
    if bar in crash_bars:
        d(CRASH, t0, 112 if bar in (3, 27) else 96)
    for b in range(4):
        tb = t0 + b * TPB
        if sec == "groove":
            if b in (0, 2):
                d(KICK, tb, 96)
            if b in (1, 3):
                d(CLAP, tb, 70)
            d(HAT, tb + TPB / 2, 62)
        else:
            d(KICK, tb, 110 if b == 0 else 100)
            if b in (1, 3):
                d(SNARE, tb, 96)
                d(CLAP, tb, 84)
            d(HAT, tb + TPB / 2, 76)
            if sec in ("A", "finale"):
                d(HAT, tb + TPB / 4, 44)
                d(HAT, tb + 3 * TPB / 4, 44)
            if sec == "B" and b == 3:
                d(OHAT, tb + TPB / 2, 64)
    # fills into sections
    if bar in (6, 14, 22):
        for s, n in enumerate((TOM_H, TOM_H, TOM_M, TOM_M, TOM_L, TOM_L, SNARE, SNARE)):
            d(n, t0 + 3 * TPB + s * TPB / 8, 70 + s * 5)
    if bar == 26:  # snare roll into the finale
        for s in range(16):
            d(SNARE, t0 + s * TPB / 4, 50 + s * 4)

# ---------- write ----------
events.sort(key=lambda e: (e[0], e[1]))
mid = mido.MidiFile(ticks_per_beat=TPB)
tr = mido.MidiTrack()
mid.tracks.append(tr)
tr.append(mido.MetaMessage("set_tempo", tempo=mido.bpm2tempo(BPM), time=0))
tr.append(mido.MetaMessage("time_signature", numerator=4, denominator=4, time=0))
last = 0
for t, _, msg in events:
    tr.append(msg.copy(time=t - last))
    last = t
tr.append(mido.MetaMessage("end_of_track", time=int(31.5 * BAR) - last if int(31.5 * BAR) > last else 0))
os.makedirs(OUT, exist_ok=True)
mid.save(os.path.join(OUT, "music.mid"))
print("wrote", os.path.join(OUT, "music.mid"), f"{mid.length:.2f}s")
