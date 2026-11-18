#!/usr/bin/env node
// Renders one Mermaid diagram to SVG or PNG in a sandboxed headless browser.
//
// It borrows Puppeteer and the Mermaid bundle from the user's @mermaid-js/mermaid-cli install,
// but renders in its own page instead of mmdc's: a blank page that cannot load anything.
//   1. Every request except data: URLs is aborted (request interception).
//   2. A Content-Security-Policy of default-src 'none' (images and fonts: data: only).
//   3. Chrome sends any http(s) traffic, loopback included, to a closed proxy port.
// So nothing in a diagram can reach the network or read a file from disk.
// --allow-external turns all three off (the user explicitly allowed includes).
//
// Usage: node mermaid-render.mjs --cli <mermaid-cli dir> -i <in.mmd> -o <out.svg|out.png>
//          [--theme default|neutral|dark|forest] [--background <css colour>]
//          [--config <mermaid.json>] [--puppeteer <puppeteer.json>] [--allow-external] [--log-requests]
// Exit 0 on success; 1 with the error on stderr.

import { readFileSync, writeFileSync } from 'node:fs'
import { createRequire } from 'node:module'
import { dirname, join } from 'node:path'
import { pathToFileURL } from 'node:url'

export const NO_NETWORK_ARGS = ['--proxy-server=http://127.0.0.1:9', '--proxy-bypass-list=<-loopback>']
// Scripts: only the inline Mermaid bundle we inject (it may build functions at runtime, hence
// 'unsafe-eval'; scripts still cannot load anything). Styles inline; images and fonts data: only.
export const CSP = "default-src 'none'; script-src 'unsafe-inline' 'unsafe-eval'; style-src 'unsafe-inline'; img-src data:; font-src data:"
const TIMEOUT_MS = 50_000
const VIEWPORT_WIDTH = 1200

function parse(argv) {
  const opts = { theme: 'default', background: 'white' }
  const names = { '--cli': 'cli', '-i': 'input', '-o': 'output', '--theme': 'theme', '--background': 'background', '--config': 'config', '--puppeteer': 'puppeteer' }
  for (let i = 0; i < argv.length; i++) {
    if (argv[i] === '--allow-external') opts.allowExternal = true
    else if (argv[i] === '--log-requests') opts.logRequests = true
    else if (names[argv[i]] && argv[i + 1] !== undefined) opts[names[argv[i]]] = argv[++i]
    else throw new Error(`mermaid-render: unexpected argument ${argv[i]}`)
  }
  for (const key of ['cli', 'input', 'output']) if (!opts[key]) throw new Error(`mermaid-render: missing ${key}`)
  return opts
}

const readJson = path => (path ? JSON.parse(readFileSync(path, 'utf8')) : {})

async function loadFromCli(cliDir) {
  const require = createRequire(join(cliDir, 'package.json'))
  let puppeteerPath
  try {
    puppeteerPath = require.resolve('puppeteer')
  } catch {
    throw new Error(`Puppeteer was not found next to mermaid-cli in ${cliDir}. Reinstall it: npm i -g @mermaid-js/mermaid-cli`)
  }
  const mod = await import(pathToFileURL(puppeteerPath).href)
  const puppeteer = mod.default ?? mod
  const mermaidDir = dirname(require.resolve('mermaid/package.json'))
  const mermaidJs = readFileSync(join(mermaidDir, 'dist', 'mermaid.min.js'), 'utf8')
  // ZenUML is an add-on diagram that mermaid-cli ships; its self-contained browser bundle is
  // injected only for ZenUML sources (it is 3 MB). Older mermaid-cli versions may lack it.
  const zenumlJs = () => {
    try {
      return readFileSync(join(dirname(require.resolve('@mermaid-js/mermaid-zenuml/package.json')), 'dist', 'mermaid-zenuml.min.js'), 'utf8')
    } catch {
      return null
    }
  }
  return { puppeteer, mermaidJs, zenumlJs }
}

// Mermaid's own detector for ZenUML: the first line that is not a comment, directive or frontmatter.
export function isZenuml(definition) {
  const body = definition.replace(/^\s*---\n[\s\S]*?\n---\s*\n/, '')
  const first = body.split('\n').map(l => l.trim()).find(l => l && !l.startsWith('%%'))
  return /^zenuml\b/.test(first ?? '')
}

export async function render(opts) {
  const definition = readFileSync(opts.input, 'utf8')
  const format = opts.output.toLowerCase().endsWith('.png') ? 'png' : 'svg'
  const fileConfig = readJson(opts.config)
  const userLaunch = readJson(opts.puppeteer)
  const { puppeteer, mermaidJs, zenumlJs } = await loadFromCli(opts.cli)
  const zenuml = isZenuml(definition) ? zenumlJs() : null
  if (isZenuml(definition) && !zenuml) {
    throw new Error('ZenUML needs @mermaid-js/mermaid-zenuml, which this mermaid-cli does not include. Update it: npm i -g @mermaid-js/mermaid-cli. Or use sequenceDiagram.')
  }

  const launch = {
    headless: 'shell',
    ...userLaunch,
    args: [...(Array.isArray(userLaunch.args) ? userLaunch.args : []), ...(opts.allowExternal ? [] : NO_NETWORK_ARGS)],
  }
  const browser = await puppeteer.launch(launch)
  try {
    const page = await browser.newPage()
    await page.setViewport({ width: VIEWPORT_WIDTH, height: 800, deviceScaleFactor: format === 'png' ? 2 : 1 })
    if (!opts.allowExternal || opts.logRequests) {
      await page.setRequestInterception(true)
      page.on('request', request => {
        const url = request.url()
        const allowed = opts.allowExternal || url.startsWith('data:') || url === 'about:blank'
        if (opts.logRequests) process.stderr.write(`${allowed ? 'allowed' : 'blocked'} ${url}\n`)
        allowed ? request.continue() : request.abort('blockedbyclient')
      })
    }
    const csp = opts.allowExternal ? '' : `<meta http-equiv="Content-Security-Policy" content="${CSP}">`
    const background = String(opts.background).replace(/[^#\w(),.% -]/g, '')
    await page.setContent(
      `<!doctype html><html><head><meta charset="utf-8">${csp}</head>` +
        `<body style="margin:0;background:${background}"><div id="container"></div></body></html>`,
    )
    if (opts.logRequests) {
      // The CSP stops most loads before they become requests; report those too.
      page.on('console', msg => msg.text().startsWith('csp-blocked ') && process.stderr.write(`blocked ${msg.text().slice(12)}\n`))
      await page.addScriptTag({ content: "document.addEventListener('securitypolicyviolation', e => console.log('csp-blocked ' + e.blockedURI))" })
    }
    // Mermaid's image shapes wait for img.decode(), which rejects when the sandbox blocks the
    // image; let it resolve so the diagram still renders, with that image left blank.
    await page.addScriptTag({
      content: 'const d = HTMLImageElement.prototype.decode; HTMLImageElement.prototype.decode = function () { return d.call(this).catch(() => {}) }',
    })
    await page.addScriptTag({ content: mermaidJs })
    // ZenUML's parser recovers from errors and only logs them (`line 2:13 mismatched input …`),
    // then draws a partial diagram; collect them so a broken source fails like any other.
    const zenumlErrors = []
    if (zenuml) {
      page.on('console', msg => {
        const text = msg.text()
        if (/^line \d+:\d+ (no viable|mismatched|extraneous|missing|token recognition)/.test(text)) zenumlErrors.push(text)
      })
      // ZenUML reads localStorage, which this blank sandboxed page may not use; give it an
      // in-memory stand-in that lasts only for this render.
      await page.addScriptTag({
        content: `(() => {
          const data = new Map()
          const storage = {
            getItem: k => (data.has(String(k)) ? data.get(String(k)) : null),
            setItem: (k, v) => void data.set(String(k), String(v)),
            removeItem: k => void data.delete(String(k)),
            clear: () => data.clear(),
            key: i => [...data.keys()][i] ?? null,
            get length() { return data.size },
          }
          Object.defineProperty(window, 'localStorage', { value: storage, configurable: true })
        })()`,
      })
      await page.addScriptTag({ content: zenuml })
      await page.evaluate(async () => {
        const plugin = globalThis.__esbuild_esm_mermaid_nm?.['mermaid-zenuml']
        await globalThis.mermaid.registerExternalDiagrams([plugin?.default ?? plugin])
      })
    }

    const config = {
      startOnLoad: false,
      ...fileConfig,
      ...(opts.theme !== 'default' ? { theme: opts.theme } : {}),
      // Never let a diagram or config loosen this: 'loose' runs click callbacks and raw HTML.
      securityLevel: 'strict',
    }
    await page.evaluate(
      async ({ definition, config, background }) => {
        const container = document.getElementById('container')
        globalThis.mermaid.initialize(config)
        const { svg } = await globalThis.mermaid.render('whiteboard-svg', definition, container)
        // Mermaid's own output, sanitized by it (securityLevel strict), placed in this sandboxed
        // page so it can be measured and serialized: the same step mermaid-cli takes.
        container.innerHTML = svg
        const el = container.querySelector('svg')
        if (el) el.style.backgroundColor = background
      },
      { definition, config, background },
    )
    if (zenumlErrors.length) throw new Error(`ZenUML parse error:\n${[...new Set(zenumlErrors)].slice(0, 5).join('\n')}`)

    if (format === 'svg') {
      const svg = await page.$eval('#container svg', el => new XMLSerializer().serializeToString(el))
      writeFileSync(opts.output, svg)
    } else {
      const clip = await page.$eval('#container svg', el => {
        const r = el.getBoundingClientRect()
        return { x: Math.floor(r.left), y: Math.floor(r.top), width: Math.ceil(r.width), height: Math.ceil(r.height) }
      })
      await page.setViewport({ width: Math.max(VIEWPORT_WIDTH, clip.x + clip.width), height: clip.y + clip.height, deviceScaleFactor: 2 })
      writeFileSync(opts.output, await page.screenshot({ clip, omitBackground: background === 'transparent' }))
    }
  } finally {
    await browser.close().catch(() => {})
  }
}

async function main() {
  let timer
  try {
    const opts = parse(process.argv.slice(2))
    await Promise.race([
      render(opts),
      new Promise((_, reject) => {
        timer = setTimeout(() => reject(new Error(`Rendering timed out after ${TIMEOUT_MS / 1000}s.`)), TIMEOUT_MS)
      }),
    ])
    return 0
  } catch (err) {
    // Puppeteer prefixes errors thrown in the page and appends the page's stack; keep Mermaid's message.
    const lines = String(err?.message ?? err).replace(/^(Evaluation failed: )?(Error: )?/, '').split('\n')
    const frame = lines.findIndex(line => /^\s+at\s|^[\w.$#]+ \((<anonymous>|https?:|file:|pptr:)/.test(line))
    process.stderr.write(`Error: ${(frame === -1 ? lines : lines.slice(0, frame)).join('\n').trim()}\n`)
    return 1
  } finally {
    clearTimeout(timer)
  }
}

const invoked = process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href
if (invoked) process.exitCode = await main()
