// Render tools/out/music.mid -> tools/out/music-raw.wav with GeneralUser GS.
// Needs: npm i spessasynth_core generaluser   (in tools/)
import * as fs from "node:fs/promises";
import { createRequire } from "node:module";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { audioToWav, BasicMIDI, SoundBankLoader, SpessaSynthProcessor, SpessaSynthSequencer } from "spessasynth_core";

const here = path.dirname(fileURLToPath(import.meta.url));
const require = createRequire(import.meta.url);
const sfPath = require.resolve("generaluser/GeneralUser.sf2");
const sf = await fs.readFile(sfPath);
const mid = await fs.readFile(path.join(here, "out/music.mid"));
const midi = BasicMIDI.fromArrayBuffer(mid.buffer.slice(mid.byteOffset, mid.byteOffset + mid.byteLength));
const bank = SoundBankLoader.fromArrayBuffer(sf.buffer.slice(sf.byteOffset, sf.byteOffset + sf.byteLength));

const sampleRate = 48000;
const synth = new SpessaSynthProcessor(sampleRate, { eventsEnabled: false });
synth.soundBankManager.addSoundBank(bank, "main");
await synth.ready;
synth.setSystemParameter("autoAllocateVoices", true);
const seq = new SpessaSynthSequencer(synth);
seq.loadNewSongList([midi]);
seq.loopCount = 0;
seq.play();

const total = Math.ceil(sampleRate * 61);
const L = new Float32Array(total);
const R = new Float32Array(total);
let filled = 0;
while (filled < total) {
  seq.processTick();
  const n = Math.min(128, total - filled);
  synth.process(L, R, filled, n);
  filled += n;
}
await fs.writeFile(path.join(here, "../assets/audio/stems/music.wav"), new Uint8Array(audioToWav([L, R], sampleRate)));
console.log("wrote assets/audio/stems/music.wav");
