import { writeFile, copyFile, mkdir } from 'node:fs/promises';
import { existsSync } from 'node:fs';
import path from 'node:path';
import sharp from 'sharp';
const root = path.resolve(import.meta.dirname, '..');
const portraits = [
  {
    id: 'lou',
    source: 'C:/Users/Lou/Downloads/Lou sandbox.png',
    width: 1334,
    height: 1179,
    crop: { left: 385, top: 30, width: 560, height: 715 },
    path: 'M 429 299 Q 418 270 426 245 Q 417 227 433 208 Q 434 181 458 166 Q 470 138 498 129 Q 515 105 548 101 Q 566 77 596 81 Q 617 63 648 73 Q 674 57 704 67 Q 733 62 755 80 Q 785 79 802 101 Q 829 105 840 137 L 853 153 Q 881 177 884 212 L 891 247 L 907 276 Q 930 312 932 356 L 934 423 Q 933 457 912 477 L 876 490 L 847 485 L 836 531 Q 826 580 803 612 L 814 664 L 823 714 Q 761 756 651 739 L 608 713 L 599 668 Q 553 652 523 615 Q 495 582 481 541 L 459 548 Q 429 550 417 527 Q 403 496 406 450 L 410 379 Q 412 344 430 329 Z',
  },
  {
    id: 'loic',
    source: 'C:/Users/Lou/Downloads/loic 2.png',
    width: 1254,
    height: 1254,
    crop: { left: 195, top: 95, width: 565, height: 700 },
    path: 'M 252 295 Q 251 251 278 215 Q 327 151 412 121 Q 501 97 592 114 Q 668 119 716 171 L 734 202 Q 759 241 746 272 L 754 295 L 742 328 L 736 378 L 746 403 L 746 465 Q 733 533 700 568 L 666 581 Q 650 632 620 675 Q 590 710 566 735 L 558 780 Q 451 810 340 765 L 334 717 Q 302 686 291 642 L 286 577 L 292 530 Q 260 529 244 505 Q 213 500 205 469 Q 197 440 207 383 L 222 337 Q 225 309 244 302 Z',
  },
  {
    id: 'loic-alt',
    source: 'C:/Users/Lou/Downloads/loic 3.png',
    width: 1254,
    height: 1254,
    crop: { left: 360, top: 76, width: 566, height: 802 },
    path: 'M 389 386 Q 379 337 388 290 Q 402 216 455 163 Q 504 111 584 94 Q 676 76 758 98 Q 839 111 885 158 Q 912 188 917 225 L 925 258 L 912 278 L 919 301 L 905 326 L 899 365 L 890 407 L 879 442 Q 890 449 885 470 L 878 500 L 877 527 L 866 546 Q 860 607 833 646 Q 815 680 798 709 L 786 765 L 793 845 Q 641 899 467 851 L 436 781 L 423 730 Q 404 670 393 615 L 383 558 Q 367 539 373 506 L 376 467 Q 366 437 378 411 Z',
  },
  {
    id: 'nico',
    source: 'C:/Users/Lou/Downloads/Nico.png',
    width: 380,
    height: 336,
    crop: { left: 112, top: 3, width: 165, height: 186 },
    path: 'M 126 57 Q 115 43 128 28 Q 141 9 164 10 Q 182 1 207 8 Q 236 7 252 30 Q 266 48 261 70 Q 274 72 269 96 Q 270 113 257 118 L 251 143 Q 240 160 221 171 L 217 182 Q 192 191 170 177 L 167 162 Q 144 152 136 130 L 129 111 Q 117 108 117 88 Q 113 71 126 66 Z',
  },
];
await mkdir(root + '/public/originals', { recursive: true });
for (const p of portraits) {
  const savedOriginal = root + '/public/originals/' + p.id + '.png';
  const source = existsSync(p.source) ? p.source : savedOriginal;
  if (path.resolve(source) !== path.resolve(savedOriginal)) await copyFile(source, savedOriginal);
  const mask = `<svg xmlns="http://www.w3.org/2000/svg" width="${p.width}" height="${p.height}"><path d="${p.path}" fill="white"/></svg>`;
  await writeFile(root + '/public/' + p.id + '-mask.svg', mask);
  const masked = await sharp(source)
    .ensureAlpha()
    .composite([{ input: Buffer.from(mask), blend: 'dest-in' }])
    .png()
    .toBuffer();
  const cropped = await sharp(masked).extract(p.crop).ensureAlpha().raw().toBuffer();
  await sharp(cropped, { raw: { width: p.crop.width, height: p.crop.height, channels: 4 } })
    .png()
    .toFile(root + '/public/' + p.id + '.png');
}
await writeFile(root + '/public/portrait-provenance.json', JSON.stringify(portraits, null, 2));
const tiles = await Promise.all(
  portraits
    .filter((p) => p.id !== 'loic-alt')
    .map(async (p, i) => ({
      input: await sharp(root + '/public/' + p.id + '.png')
        .resize({ height: 390 })
        .png()
        .toBuffer(),
      left: 80 + i * 360,
      top: 60,
    })),
);
await sharp({ create: { width: 1160, height: 500, channels: 3, background: '#071a29' } })
  .composite(tiles)
  .png()
  .toFile(root + '/analysis/portraits.png');
