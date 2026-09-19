#!/usr/bin/env node
/**
 * Check every Mermaid diagram in the built site with Mermaid's own parser.
 *
 * MkDocs only copies the diagram's text into the HTML — whether the syntax is
 * valid is decided in the browser, where a mistake shows up as an error box
 * instead of a picture. This runs the real parser over `site/**` so a broken
 * diagram fails here instead of on the page.
 *
 *   npm install jsdom          # once, in this directory
 *   .venv/bin/mkdocs build --strict
 *   node tools/check-mermaid.cjs
 *
 * Mermaid's bundle is browser-oriented: it wants a DOM while it loads, and its
 * trailing export line assumes a `<script>` global. So this sets up a jsdom
 * window first, and loads the bundle from a temporary copy with that trailing
 * line replaced by an explicit global export.
 */
"use strict";

const fs = require("node:fs");
const os = require("node:os");
const path = require("node:path");

const REPO = path.resolve(__dirname, "..");
const BUNDLE = path.join(REPO, "docs", "javascripts", "mermaid.min.js");
const SITE = path.join(REPO, "site");

let JSDOM;
try {
  ({ JSDOM } = require(path.join(REPO, "node_modules", "jsdom")));
} catch {
  console.error("jsdom is required: run `npm install jsdom` in " + REPO);
  process.exit(2);
}

// A DOM before the bundle loads: mermaid reads `document` at import time.
const dom = new JSDOM("<!doctype html><html><body></body></html>", { pretendToBeVisual: true });

// Node 22 already defines some of these, and `navigator` is getter-only there,
// so each is defined rather than assigned and a failure is not fatal.
function define(name, value) {
  try {
    Object.defineProperty(globalThis, name, { value, writable: true, configurable: true });
  } catch {
    /* already present and not replaceable: good enough for the parser */
  }
}

define("window", dom.window);
define("document", dom.window.document);
define("navigator", dom.window.navigator);
define("HTMLElement", dom.window.HTMLElement);
define("SVGElement", dom.window.SVGElement);
define("Element", dom.window.Element);
define("Node", dom.window.Node);
define("DOMParser", dom.window.DOMParser);
define("addEventListener", () => {});
define("removeEventListener", () => {});

const source = fs.readFileSync(BUNDLE, "utf8").trimEnd().split("\n");
if (source[source.length - 1].includes('globalThis["mermaid"]')) source.pop();
source.push("globalThis.__mermaid_ns = __esbuild_esm_mermaid_nm;");
const prepared = path.join(fs.mkdtempSync(path.join(os.tmpdir(), "kelp-mermaid-")), "mermaid.cjs");
fs.writeFileSync(prepared, source.join("\n") + "\n");
require(prepared);

const namespace = globalThis.__mermaid_ns?.mermaid;
const mermaid = namespace?.default ?? namespace;
if (!mermaid?.parse) {
  console.error("could not load mermaid from " + BUNDLE);
  process.exit(2);
}

function htmlFiles(dir) {
  return fs.readdirSync(dir).flatMap((entry) => {
    const full = path.join(dir, entry);
    return fs.statSync(full).isDirectory() ? htmlFiles(full) : [full];
  });
}

function diagramText(html) {
  return html
    .replace(/<\/?code>/g, "")
    .replace(/&lt;/g, "<")
    .replace(/&gt;/g, ">")
    .replace(/&amp;/g, "&")
    .replace(/&quot;/g, '"');
}

(async () => {
  if (!fs.existsSync(SITE)) {
    console.error("no site/ directory — build first: .venv/bin/mkdocs build --strict");
    process.exit(2);
  }
  let checked = 0;
  let failed = 0;
  for (const file of htmlFiles(SITE).filter((f) => f.endsWith(".html"))) {
    const html = fs.readFileSync(file, "utf8");
    for (const match of html.matchAll(/<pre class="mermaid">([\s\S]*?)<\/pre>/g)) {
      checked += 1;
      try {
        await mermaid.parse(diagramText(match[1]));
      } catch (error) {
        failed += 1;
        console.error(`FAIL ${path.relative(SITE, file)}: ${String(error.message).split("\n")[0]}`);
      }
    }
  }
  console.log(`checked ${checked} diagram(s), ${failed} failed`);
  // `process.exit()` here would drop the line above when stdout is a pipe.
  process.exitCode = failed === 0 ? 0 : 1;
})();
