// node tts.cjs "<teks>" out.wav [voice] [speed] [pitch]
const t2w = require("text2wav");
const fs = require("fs");
(async () => {
  const [txt, out, voice, speed, pitch] = process.argv.slice(2);
  const wav = await t2w(txt, { voice: voice || "ms+m3", speed: +(speed || 155), pitch: +(pitch || 48) });
  fs.writeFileSync(out, wav);
})();
