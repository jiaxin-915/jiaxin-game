// Rasterize our code-native SVG UI for the SPX renderer; no user images are edited.
const fs = require('node:fs/promises');
const path = require('node:path');
const sharp = require('sharp');
const root = path.resolve(__dirname, '../..');
(async () => {
  const items = JSON.parse(await fs.readFile(path.join(root, 'game/ui-source/render-manifest.json'), 'utf8'));
  for (const item of items) {
    const output = path.join(root, item.output);
    await fs.mkdir(path.dirname(output), {recursive: true});
    await sharp(path.join(root, item.source)).png().toFile(output);
  }
  console.log(`Rendered ${items.length} UI assets.`);
})().catch(e => { console.error(e); process.exit(1); });
