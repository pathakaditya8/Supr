// Generates src/dark.css from src/styles.css.
//
// For every rule that sets a colour, it writes a copy under html[data-theme="dark"] with the colour moved to a dark
// theme equivalent: light surfaces become dark, dark text becomes light, light borders become dark. Colours that are
// already dark (footer, brand buttons) or already light (white text on them) are left alone.
// Hand-made fixes live in src/dark-overrides.css, which is loaded after the generated file.
//
// Run from frontend/:  npm run dark-css
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import postcss from 'postcss';

const here = path.dirname(fileURLToPath(import.meta.url));
const src = path.join(here, '..', 'src', 'styles.css');
const out = path.join(here, '..', 'src', 'dark.css');
const PREFIX = 'html[data-theme="dark"]';

// ---- colour maths -------------------------------------------------------------------------------------------
const clamp = (v, lo, hi) => Math.min(hi, Math.max(lo, v));
function toHsl([r, g, b]) {
  r /= 255; g /= 255; b /= 255;
  const max = Math.max(r, g, b), min = Math.min(r, g, b), l = (max + min) / 2;
  if (max === min) return [0, 0, l];
  const d = max - min, s = l > 0.5 ? d / (2 - max - min) : d / (max + min);
  const h = max === r ? (g - b) / d + (g < b ? 6 : 0) : max === g ? (b - r) / d + 2 : (r - g) / d + 4;
  return [h * 60, s, l];
}
function fromHsl([h, s, l]) {
  const c = (1 - Math.abs(2 * l - 1)) * s, x = c * (1 - Math.abs(((h / 60) % 2) - 1)), m = l - c / 2;
  const [r, g, b] = h < 60 ? [c, x, 0] : h < 120 ? [x, c, 0] : h < 180 ? [0, c, x] : h < 240 ? [0, x, c] : h < 300 ? [x, 0, c] : [c, 0, x];
  return [r, g, b].map(v => Math.round((v + m) * 255));
}
// near-white and greyish colours (cream, ivory, light grey) count as neutral
const neutral = ([r, g, b]) => (Math.max(r, g, b) - Math.min(r, g, b)) / 255 < 0.09;
const hex2 = n => n.toString(16).padStart(2, '0');

function parseColor(text) {
  text = text.trim().toLowerCase();
  if (text === 'white') return { rgb: [255, 255, 255], a: 1 };
  if (text === 'black') return { rgb: [0, 0, 0], a: 1 };
  let m = /^#([0-9a-f]{3,8})$/.exec(text);
  if (m) {
    let h = m[1];
    if (h.length === 3 || h.length === 4) h = [...h].map(c => c + c).join('');
    if (h.length !== 6 && h.length !== 8) return null;
    return { rgb: [0, 2, 4].map(i => parseInt(h.slice(i, i + 2), 16)), a: h.length === 8 ? parseInt(h.slice(6, 8), 16) / 255 : 1 };
  }
  m = /^rgba?\(\s*([\d.]+)[\s,]+([\d.]+)[\s,]+([\d.]+)(?:\s*[,/]\s*([\d.]+%?))?\s*\)$/.exec(text);
  if (m) {
    let a = m[4] === undefined ? 1 : m[4].endsWith('%') ? parseFloat(m[4]) / 100 : parseFloat(m[4]);
    return { rgb: [m[1], m[2], m[3]].map(Number), a };
  }
  return null;
}
function format({ rgb, a }) {
  return a >= 0.999 ? `#${rgb.map(hex2).join('')}` : `rgba(${rgb.join(',')},${Math.round(a * 1000) / 1000})`;
}

// Per kind of property: how a light-theme colour becomes a dark-theme colour.
const mappers = {
  surface(c) {                       // backgrounds: light surfaces turn dark, dark/brand surfaces stay
    const [h, s, l] = toHsl(c.rgb);
    if (l < 0.78) return c;
    const nl = l >= 0.99 ? 0.13 : clamp(0.13 + (0.995 - l) * 0.75, 0.11, 0.3);
    return { rgb: fromHsl(neutral(c.rgb) ? [195, 0.14, nl] : [h, s * 0.55, nl]), a: c.a };   // cream and white follow the site's cool teal-grey
  },
  text(c) {                          // text and icons: dark text turns light, light text stays
    const [h, s, l] = toHsl(c.rgb);
    if (l >= 0.62) return c;
    return { rgb: fromHsl([h, s * 0.8, clamp(1 - l * 0.92, 0.66, 0.93)]), a: c.a };
  },
  line(c) {                          // borders and rings
    const [h, s, l] = toHsl(c.rgb);
    if (l < 0.72) return c;
    return { rgb: fromHsl(neutral(c.rgb) ? [195, 0.12, clamp(0.12 + (1 - l) * 1.15, 0.12, 0.35)] : [h, s * 0.5, clamp(0.12 + (1 - l) * 1.15, 0.12, 0.35)]), a: c.a };
  },
};
const COLOR_TOKEN = /#[0-9a-fA-F]{3,8}\b|rgba?\([^)]*\)|\bwhite\b|\bblack\b/g;
function mapValue(value, kind) {
  return value.replace(COLOR_TOKEN, token => {
    const parsed = parseColor(token);
    if (!parsed) return token;
    return format(mappers[kind](parsed));
  });
}
const kindOf = prop => {
  if (/^(background|background-color|background-image)$/.test(prop)) return 'surface';
  if (/^(color|fill|stroke|caret-color|text-decoration-color|-webkit-text-fill-color)$/.test(prop)) return 'text';
  if (/^(border|border-(top|right|bottom|left)|border-color|border-(top|right|bottom|left)-color|outline|outline-color|column-rule|box-shadow)$/.test(prop)) return 'line';
  return null;
};

// ---- selectors ----------------------------------------------------------------------------------------------
function darkSelector(selector) {
  return selector.split(',').map(part => {
    part = part.trim();
    if (/^:root\b/.test(part)) return part.replace(/^:root/, PREFIX);
    if (/^html\b/.test(part)) return part.replace(/^html/, PREFIX);
    return `${PREFIX} ${part}`;
  }).join(',');
}

// ---- walk ---------------------------------------------------------------------------------------------------
function darkNodes(container) {
  const nodes = [];
  container.each(node => {
    if (node.type === 'atrule') {
      if (/keyframes|font-face/.test(node.name)) return;
      if (node.nodes) {
        const inner = darkNodes(node);
        if (inner.length) nodes.push(postcss.atRule({ name: node.name, params: node.params }).append(inner));
      }
      return;
    }
    if (node.type !== 'rule') return;
    const decls = [];
    node.each(d => {
      if (d.type !== 'decl' || d.prop.startsWith('--')) return;
      const kind = kindOf(d.prop);
      if (!kind) return;
      let value = d.value;
      // brand colour written as a variable: as text it must be a lighter teal on a dark surface
      if (kind === 'text') value = value.replace(/var\(--green\)/g, 'var(--text-brand)');
      const mapped = mapValue(value, kind);
      if (mapped !== d.value) decls.push(postcss.decl({ prop: d.prop, value: mapped, important: d.important }));
    });
    if (decls.length) nodes.push(postcss.rule({ selector: darkSelector(node.selector) }).append(decls));
  });
  return nodes;
}

const css = postcss.parse(fs.readFileSync(src, 'utf8'));
const generated = darkNodes(css);
const header = '/* Generated by scripts/make-dark-css.mjs from styles.css. Do not edit by hand; put fixes in dark-overrides.css. */\n';
fs.writeFileSync(out, header + generated.map(n => n.toString()).join('\n') + '\n');
console.log(`dark.css: ${generated.length} rules, ${(fs.statSync(out).size / 1024).toFixed(1)} KB`);
