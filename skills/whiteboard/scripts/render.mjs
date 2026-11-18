#!/usr/bin/env node
// Renders a Mermaid, D2 or PlantUML diagram to SVG with the CLI installed on this machine.
// No dependencies beyond Node 18+. Run with --help for usage.
//
// Exit codes: 0 rendered, 1 render failed (the message says why: fix the source and run again),
// 2 bad arguments, 3 renderer not installed.

import { spawn, spawnSync } from 'node:child_process'
import { existsSync, lstatSync, mkdirSync, mkdtempSync, readFileSync, readdirSync, realpathSync, renameSync, rmSync, statSync, writeFileSync } from 'node:fs'
import { tmpdir } from 'node:os'
import { basename, delimiter, dirname, extname, join, relative, resolve } from 'node:path'
import { fileURLToPath, pathToFileURL } from 'node:url'

export const VERSION = '1.1.1'
export const RENDER_TIMEOUT_MS = 60_000
export const MAX_TITLE = 80

export const LANGUAGES = ['mermaid', 'd2', 'plantuml']
export const THEMES = ['default', 'neutral', 'dark', 'forest']

export const RENDERERS = {
  mermaid: { bin: 'mmdc', env: 'WHITEBOARD_MMDC', ext: 'mmd', label: 'Mermaid', install: 'npm i -g @mermaid-js/mermaid-cli', versionArg: '--version' },
  d2: { bin: 'd2', env: 'WHITEBOARD_D2', ext: 'd2', label: 'D2', install: 'brew install d2, or see https://d2lang.com/tour/install', versionArg: '--version' },
  plantuml: { bin: 'plantuml', env: 'WHITEBOARD_PLANTUML', ext: 'puml', label: 'PlantUML', install: 'brew install plantuml, or apt install plantuml (needs Java)', versionArg: '-version' },
}

const EXTENSIONS = { mmd: 'mermaid', mermaid: 'mermaid', d2: 'd2', puml: 'plantuml', plantuml: 'plantuml', pu: 'plantuml', iuml: 'plantuml', wsd: 'plantuml' }

const SYNTAX_ERROR =
  /Parse error|Syntax error|Lexical error|No diagram type detected|UnknownDiagramError|^err:|\berr: |failed to compile|Error line \d+/im

// A frame of the stack mmdc prints after the message: `    at fn (file:...)` or `Parser.parse (https://...)`.
const STACK_FRAME = /^\s+at\s|^[\w.$#]+ \((?:<anonymous>|pptr:|https?:\/\/|file:\/\/)/

const USAGE = `whiteboard render ${VERSION}

Usage:
  node render.mjs --title "<title>" [options] < diagram-source
  node render.mjs --title "<title>" --file <path> [options]
  node render.mjs --doctor

Options:
  --title <text>      Diagram title (required, at most ${MAX_TITLE} characters). It names the files.
  --file <path>       Read the source from a file instead of stdin.
  --language <name>   mermaid (default) | d2 | plantuml. Guessed from --file's extension,
                      a fence such as \`\`\`d2, or @startuml when omitted.
  --out <dir>         Output folder (default: diagrams, relative to the current folder).
  --theme <name>      default | neutral | dark | forest   (env WHITEBOARD_THEME)
  --config <file>     Mermaid JSON config file             (env WHITEBOARD_MERMAID_CONFIG)
  --png               Also write a PNG next to the SVG.
  --check             Only validate: render to a temporary folder and write nothing.
  --open              Open the SVG in the default viewer.
  --share             Upload the source to a secret GitHub gist with the gh CLI and print the link.
                      Only when the user asked for it.
  --json              Print the result as JSON.
  --doctor            Check which renderers are installed and that they work.

Renderer paths can be pinned with WHITEBOARD_MMDC, WHITEBOARD_D2 and WHITEBOARD_PLANTUML.
Redrawing an existing title moves the previous files to <out>/.versions/<name>/.`

// ---------------------------------------------------------------- pure helpers

// Keeps a diagram from reading local files, environment variables or URLs into the image.
// A diagram drawn from untrusted content (a README, an issue) could otherwise leak secrets
// into a file the user shares. The checks are deliberately strict: a false positive costs a
// rewrite, a miss costs a leak.

// PlantUML preprocessor directives that cannot touch files, the network or the environment.
// Every other `!` directive is refused. `!include <...>` loads PlantUML's bundled library.
const PLANTUML_ALLOWED = new RegExp(
  '^!(' + [
    'include\\s*<[\\w./-]+>\\s*$',
    'theme\\s+[\\w-]+\\s*$',
    '\\$',
    ...['define', 'definelong', 'enddefinelong', 'undef', 'pragma', 'procedure', 'endprocedure', 'function', 'endfunction',
      'unquoted', 'final', 'return', 'if', 'ifdef', 'ifndef', 'else', 'elseif', 'endif', 'while', 'endwhile', 'foreach',
      'endfor', 'log', 'assert', 'local', 'global', 'startsub', 'endsub'].map(d => `${d}\\b`),
  ].join('|') + ')',
  'i',
)

const ANYWHERE = {
  // Built-ins that read files or env, or call other built-ins by name; <img:...> loads an image file or URL.
  plantuml: [/%\s*(getenv|load_json|loadjson|file_exists|dirpath|filename|filenamenoextension|call_user_func|invoke_procedure|get_variable_value)\s*\(/i, /<img\s*:/i],
  // Imports: `...@file`, `key: @file`, `[@a; @b]`, quoted or not, wherever they sit on a line.
  d2: [/(\.\.\.|:|\[|;)\s*["']?@/],
  // Mermaid needs no source checks: mermaid-render.mjs renders it in a page that cannot load
  // anything from the network or disk, whatever the diagram contains.
}

function lineAt(source, index) {
  const start = source.lastIndexOf('\n', index - 1) + 1
  const end = source.indexOf('\n', index)
  return source.slice(start, end === -1 ? undefined : end).trim()
}

// Returns the offending line, so the message shows the agent exactly what to change.
export function unsafeDirective(language, source) {
  if (language === 'plantuml') {
    for (const raw of source.split(/\r?\n/)) {
      const line = raw.trim()
      if (line.startsWith('!') && !PLANTUML_ALLOWED.test(line)) return line
    }
  }
  for (const pattern of ANYWHERE[language] ?? []) {
    const m = pattern.exec(source)
    if (m) return lineAt(source, m.index)
  }
  return null
}

// D2 draws PNGs in a browser and bundles every image first, so icons, markdown or HTML blocks
// and any URL or file reference would be fetched or read into the image. SVGs keep them as links.
// Deliberately broad: any block string (`key: |...|`, whatever its delimiter), any HTML tag or
// entity, any URL-like text. Plain boxes, arrows and labels still get a PNG.
export function hasD2External(source) {
  return /\bicon\s*:|:\s*\||<[a-z!/?]|&(#|[a-z]+;)|!\[|[a-z][\w+.-]*:\/\/|\bfile:|url\s*\(|\\/i.test(source)
}

const MERMAID_CLI = '@mermaid-js/mermaid-cli'
const MERMAID_HELPER = () => process.env.WHITEBOARD_MERMAID_RENDERER || join(dirname(fileURLToPath(import.meta.url)), 'mermaid-render.mjs')

function isMermaidCli(dir) {
  try {
    return JSON.parse(readFileSync(join(dir, 'package.json'), 'utf8')).name === MERMAID_CLI
  } catch {
    return false
  }
}

// The @mermaid-js/mermaid-cli package folder behind an mmdc binary: up from the binary's real
// path (npm and Homebrew symlink it), or beside it (npm's Windows .cmd shims, nvm and npm prefixes).
export function mermaidCliDir(bin) {
  const pinned = process.env.WHITEBOARD_MERMAID_CLI_DIR
  if (pinned) return isMermaidCli(pinned) || process.env.WHITEBOARD_MERMAID_RENDERER ? pinned : null
  let dir
  try {
    dir = dirname(realpathSync(bin))
  } catch {
    dir = dirname(bin)
  }
  for (let i = 0; i < 6 && dir !== dirname(dir); i++, dir = dirname(dir)) if (isMermaidCli(dir)) return dir
  const near = [join(dirname(bin), 'node_modules', MERMAID_CLI), join(dirname(bin), '..', 'lib', 'node_modules', MERMAID_CLI)]
  return near.find(isMermaidCli) ?? null
}

export function slug(title) {
  const s = title
    .normalize('NFKD')
    .replace(/[̀-ͯ]/g, '')
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '')
    .slice(0, 60)
    .replace(/-+$/, '')
  return s || 'diagram'
}

export function cleanTitle(title) {
  return String(title ?? '').replace(/[\u0000-\u001f\u007f-\u009f]+/g, ' ').replace(/\s+/g, ' ').trim()
}

// Removes one surrounding ``` or ~~~ fence and returns its info string as the language hint.
export function stripFences(text) {
  const t = text.replace(/^﻿/, '').trim()
  const m = /^(`{3,}|~{3,})([^\n]*)\n([\s\S]*?)\n?\1\s*$/.exec(t)
  return m ? { source: m[3].trim(), hint: m[2].trim().toLowerCase() } : { source: t, hint: '' }
}

export function languageFrom({ flag, file, hint, source }) {
  if (flag) return LANGUAGES.includes(flag) ? flag : null
  if (hint && LANGUAGES.includes(hint)) return hint
  if (hint === 'puml') return 'plantuml'
  if (file) {
    const byExt = EXTENSIONS[extname(file).slice(1).toLowerCase()]
    if (byExt) return byExt
  }
  return /^@start(uml|mindmap|gantt|wbs|json|yaml|salt)\b/m.test(source) ? 'plantuml' : 'mermaid'
}

export function fenceBlock(language, source) {
  const longest = Math.max(0, ...(source.match(/`+/g) ?? []).map(run => run.length))
  const fence = '`'.repeat(Math.max(3, longest + 1))
  return `${fence}${language}\n${source}\n${fence}`
}

export function renderArgv(language, { input, output, dir, format, theme, mermaidConfig, puppeteerConfig, helper, cliDir, allowExternal }) {
  const dark = theme === 'dark'
  switch (language) {
    case 'mermaid':
      // Runs under `node`: our sandboxed renderer, using the mermaid-cli install's Puppeteer and Mermaid.
      return [
        helper, '--cli', cliDir, '-i', input, '-o', output, '--background', dark ? '#1e1e1e' : 'white',
        ...(theme !== 'default' ? ['--theme', theme] : []),
        ...(mermaidConfig ? ['--config', mermaidConfig] : []),
        ...(puppeteerConfig ? ['--puppeteer', puppeteerConfig] : []),
        ...(allowExternal ? ['--allow-external'] : []),
      ]
    case 'd2':
      // --bundle=false: leave icon URLs as links instead of fetching them at render time.
      return [...(dark ? ['--theme=200'] : []), '--pad=24', ...(format === 'svg' ? ['--bundle=false'] : []), input, output]
    case 'plantuml':
      return [`-t${format}`, ...(dark ? ['-darkmode'] : []), '-o', dir, input]
  }
  throw new Error(`unknown language ${language}`)
}

export function failureOf({ status, stderr, stdout }) {
  const lines = String(stderr || stdout || '').trim().split(/\r?\n/)
  const firstFrame = lines.findIndex(line => STACK_FRAME.test(line))
  const text = (firstFrame === -1 ? lines : lines.slice(0, firstFrame)).join('\n').trim().slice(0, 2000)
  return {
    kind: SYNTAX_ERROR.test(text) ? 'syntax' : 'failed',
    message: text || `The renderer exited with code ${status}.`,
  }
}

// Newest first: nvm folder names (v22.10.1) by numeric parts; anything else last.
export function byNewestVersion(a, b) {
  const parts = s => /^v?(\d+)\.(\d+)\.(\d+)/.exec(s)?.slice(1).map(Number)
  const pa = parts(a)
  const pb = parts(b)
  if (!pa || !pb) return pa ? -1 : pb ? 1 : a.localeCompare(b)
  for (let i = 0; i < 3; i++) if (pa[i] !== pb[i]) return pb[i] - pa[i]
  return 0
}

export function parseArgs(argv) {
  const flags = new Set(['png', 'check', 'open', 'share', 'json', 'doctor', 'help', 'version'])
  const values = new Set(['title', 'file', 'language', 'out', 'theme', 'config'])
  const opts = {}
  for (let i = 0; i < argv.length; i++) {
    const arg = argv[i]
    if (arg === '-h') { opts.help = true; continue }
    if (!arg.startsWith('--')) throw new UsageError(`Unexpected argument: ${arg}`)
    const [name, inline] = arg.slice(2).split(/=(.*)/s, 2)
    if (flags.has(name)) opts[name] = true
    else if (values.has(name)) {
      const value = inline ?? argv[++i]
      if (value === undefined) throw new UsageError(`--${name} needs a value`)
      opts[name] = value
    } else throw new UsageError(`Unknown option: --${name}`)
  }
  return opts
}

export class UsageError extends Error {}

// ---------------------------------------------------------------- finding renderers

const isWindows = process.platform === 'win32'

function isFile(path) {
  try {
    return statSync(path).isFile()
  } catch {
    return false
  }
}

function onPath(bin, pathVar) {
  const exts = isWindows ? (process.env.PATHEXT || '.EXE;.CMD;.BAT').split(';').concat('') : ['']
  for (const dir of (pathVar || '').split(delimiter).filter(Boolean)) {
    for (const ext of exts) {
      const candidate = join(dir, bin + ext.toLowerCase())
      if (isFile(candidate)) return candidate
      const upper = join(dir, bin + ext)
      if (ext && isFile(upper)) return upper
    }
  }
  return null
}

// GUI-launched agents often run without the login shell's PATH, so ask the shell, then look
// where npm, nvm and Homebrew put binaries.
function fallbackLookup(bin) {
  if (process.env.WHITEBOARD_LOOKUP === 'path') return null
  if (!isWindows) {
    const shell = process.env.SHELL && existsSync(process.env.SHELL) ? process.env.SHELL : '/bin/sh'
    const run = spawnSync(shell, ['-lc', `command -v ${bin}`], { encoding: 'utf8', timeout: 5_000 })
    const found = (run.stdout || '').split(/\r?\n/).map(l => l.trim()).filter(l => l.startsWith('/')).pop()
    if (run.status === 0 && found && isFile(found)) return found
  }
  const home = process.env.HOME || process.env.USERPROFILE || ''
  const dirs = isWindows
    ? [process.env.APPDATA && join(process.env.APPDATA, 'npm')].filter(Boolean)
    : ['/opt/homebrew/bin', '/usr/local/bin', '/usr/bin', '/snap/bin', home && join(home, '.local/bin')].filter(Boolean)
  const nvm = home && join(home, '.nvm', 'versions', 'node')
  if (nvm && existsSync(nvm)) {
    for (const v of readdirSync(nvm).sort(byNewestVersion)) dirs.push(join(nvm, v, 'bin'))
  }
  return onPath(bin, dirs.join(delimiter))
}

export function findRenderer(language) {
  const r = RENDERERS[language]
  const pinned = process.env[r.env]
  if (pinned && !isFile(pinned)) return { error: `${r.env} is set to ${pinned}, which does not exist.` }
  const path = pinned || onPath(r.bin, process.env.PATH) || fallbackLookup(r.bin)
  if (!path) return { error: `${r.bin} (${r.label}) was not found. Install it with: ${r.install}. Or set ${r.env} to its full path.` }
  if (language !== 'mermaid') return { path }
  const cliDir = mermaidCliDir(path)
  return cliDir
    ? { path, cliDir }
    : { error: `Found ${path} but not the ${MERMAID_CLI} package behind it. Reinstall with: ${r.install}. Or set WHITEBOARD_MERMAID_CLI_DIR to the package folder.` }
}

// ---------------------------------------------------------------- running renderers

const allowIncludes = () => process.env.WHITEBOARD_ALLOW_INCLUDES === '1'

function run(bin, args, { timeout = RENDER_TIMEOUT_MS, cwd } = {}) {
  // mmdc is a Node script: put its folder first on PATH so `#!/usr/bin/env node` finds the node it was installed with.
  const env = { ...process.env, PATH: [dirname(bin), process.env.PATH].filter(Boolean).join(delimiter) }
  // PlantUML's SANDBOX profile blocks file, URL and environment access from inside diagrams.
  if (!allowIncludes()) env.PLANTUML_SECURITY_PROFILE = 'SANDBOX'
  const viaShell = isWindows && /\.(cmd|bat)$/i.test(bin)
  const quote = s => `"${String(s).replace(/"/g, '""')}"`
  const result = viaShell
    ? spawnSync([bin, ...args].map(quote).join(' '), { shell: true, encoding: 'utf8', timeout, env, cwd, windowsHide: true })
    : spawnSync(bin, args, { encoding: 'utf8', timeout, env, cwd, windowsHide: true })
  return result
}

export function renderTo(language, renderer, source, { dir, format = 'svg', theme = 'default', mermaidConfig = '' }) {
  const r = RENDERERS[language]
  const input = join(dir, `diagram.${r.ext}`)
  const output = join(dir, `diagram.${format}`)
  writeFileSync(input, source.endsWith('\n') ? source : `${source}\n`)
  const mermaid = language === 'mermaid'
  const argv = renderArgv(language, {
    input, output, dir, format, theme, mermaidConfig,
    puppeteerConfig: process.env.WHITEBOARD_PUPPETEER_CONFIG || '',
    helper: MERMAID_HELPER(),
    cliDir: renderer.cliDir,
    allowExternal: allowIncludes(),
  })
  // Run from the empty work folder, so any relative path inside the diagram resolves to nothing.
  const result = run(mermaid ? process.execPath : renderer.path, argv, { cwd: dir, timeout: RENDER_TIMEOUT_MS })
  if (result.error) {
    const timedOut = result.error.code === 'ETIMEDOUT' || result.signal === 'SIGTERM'
    return {
      ok: false,
      kind: timedOut ? 'timeout' : 'failed',
      message: timedOut
        ? `Rendering took longer than ${RENDER_TIMEOUT_MS / 1000}s and was stopped. Simplify or split the diagram.`
        : `The renderer could not run: ${result.error.message}`,
    }
  }
  const produced = isFile(output) ? readFileSync(output) : null
  const valid = produced && (format === 'png' ? produced.subarray(1, 4).toString() === 'PNG' : /<svg[\s>]/.test(produced.subarray(0, 4096).toString()))
  // PlantUML can exit 0 on a syntax error and draw the error into the image instead; newer
  // versions also print "Error line N".
  if (language === 'plantuml' && valid) {
    const printed = /Error line \d+|Syntax Error/i.test(`${result.stderr}${result.stdout}`)
    const drawn = format === 'svg' && /Syntax Error\?/i.test(produced.toString())
    if (printed || drawn) {
      const texts = drawn ? [...produced.toString().matchAll(/<text[^>]*>([^<]*)<\/text>/g)].map(m => m[1].trim()).filter(Boolean) : []
      const failure = failureOf(result)
      return {
        ok: false,
        kind: 'syntax',
        message: printed ? failure.message : `PlantUML reported a syntax error: ${texts.join(' ').slice(0, 500) || 'see the source'}`,
      }
    }
  }
  if (result.status !== 0 || !valid) return { ok: false, ...failureOf(result) }
  return { ok: true, path: output, bytes: produced.length }
}

// ---------------------------------------------------------------- saving

export class UnsafePathError extends Error {}

function isLink(path) {
  try {
    return lstatSync(path).isSymbolicLink()
  } catch {
    return false
  }
}

// Writes through a temporary file renamed into place, so the target is replaced, never followed.
function writeReplacing(target, data) {
  const tmp = `${target}.${process.pid}.tmp`
  writeFileSync(tmp, data, { flag: 'wx' })
  renameSync(tmp, target)
}

// Saves the source and rendered files as <out>/<name>.*. When the title was drawn before with a
// different source, the earlier files move to <out>/.versions/<name>/<n>/ first.
// Symbolic links among the files it writes or moves are refused: a planted link could
// otherwise redirect the write to any file the user can change.
export function save({ outDir, name, ext, source, sourceFile, rendered }) {
  mkdirSync(outDir, { recursive: true })
  const sourcePath = join(outDir, `${name}.${ext}`)
  const sameFile = Boolean(sourceFile) && resolve(sourceFile) === resolve(sourcePath)
  const exts = ['svg', 'png', ...new Set(Object.values(RENDERERS).map(r => r.ext))]
  const candidates = [...exts.map(e => join(outDir, `${name}.${e}`)), join(outDir, '.versions'), join(outDir, '.versions', name)]
  const link = candidates.find(isLink)
  if (link) throw new UnsafePathError(`${link} is a symbolic link; refusing to write through it. Remove it or pick another --title or --out.`)
  const existing = exts.map(e => join(outDir, `${name}.${e}`)).filter(isFile)
  const unchanged = sameFile || (isFile(sourcePath) && readFileSync(sourcePath, 'utf8').trim() === source.trim())
  const versions = join(outDir, '.versions', name)
  const archived = () =>
    existsSync(versions) ? Math.max(0, ...readdirSync(versions).map(n => Number.parseInt(n, 10)).filter(Number.isFinite)) : 0
  if (!unchanged && existing.length > 0) {
    const dir = join(versions, String(archived() + 1))
    mkdirSync(dir, { recursive: true })
    for (const file of existing) renameSync(file, join(dir, basename(file)))
  }
  const version = archived() + 1
  if (!sameFile) writeReplacing(sourcePath, source.endsWith('\n') ? source : `${source}\n`)
  const written = { source: sourcePath }
  for (const [format, path] of Object.entries(rendered)) {
    const target = join(outDir, `${name}.${format}`)
    writeReplacing(target, readFileSync(path))
    written[format] = target
  }
  return { written, version }
}

// ---------------------------------------------------------------- side actions

function openFile(path) {
  const [cmd, args] =
    process.platform === 'darwin' ? ['open', [path]]
    : isWindows ? ['cmd', ['/c', 'start', '""', path]]
    : ['xdg-open', [path]]
  const child = spawn(cmd, args, { detached: true, stdio: 'ignore', windowsHide: true })
  child.on('error', () => {})
  child.unref()
}

function shareGist(title, language, source, dir) {
  const gh = onPath('gh', process.env.PATH) ?? fallbackLookup('gh')
  if (!gh) return { ok: false, message: 'The GitHub CLI (gh) was not found. Install it from https://cli.github.com and run gh auth login.' }
  const file = join(dir, `${slug(title)}.md`)
  writeFileSync(file, `# ${title}\n\n${fenceBlock(language, source)}\n`)
  const result = run(gh, ['gist', 'create', '--desc', title, file], { timeout: 30_000 })
  const url = (result.stdout || '').split(/\s+/).find(s => s.startsWith('https://'))
  return url ? { ok: true, url } : { ok: false, message: (result.stderr || 'gh gist create failed.').trim() }
}

// ---------------------------------------------------------------- doctor

const SAMPLES = {
  mermaid: 'flowchart LR\n  A[whiteboard] --> B[ok]',
  d2: 'whiteboard -> ok',
  plantuml: '@startuml\nwhiteboard -> ok\n@enduml',
}

export function doctor() {
  const checks = []
  const [major] = process.versions.node.split('.').map(Number)
  checks.push({ label: 'Node.js', ok: major >= 18, detail: `v${process.versions.node}${major >= 18 ? '' : ' (needs 18 or newer)'}` })
  for (const language of LANGUAGES) {
    const r = RENDERERS[language]
    const found = findRenderer(language)
    if (!found.path) {
      checks.push({ label: r.label, ok: language === 'mermaid' ? false : null, detail: found.error })
      continue
    }
    const dir = mkdtempSync(join(tmpdir(), 'whiteboard-doctor-'))
    try {
      const result = renderTo(language, found, SAMPLES[language], { dir })
      checks.push({ label: r.label, ok: result.ok, detail: result.ok ? `${found.path} renders` : `${found.path} failed a test render: ${result.message}` })
    } finally {
      rmSync(dir, { recursive: true, force: true })
    }
  }
  const gh = onPath('gh', process.env.PATH) ?? fallbackLookup('gh')
  checks.push({ label: 'GitHub CLI (for --share)', ok: gh ? true : null, detail: gh ?? 'not installed (optional)' })
  return checks
}

function formatChecks(checks) {
  const mark = ok => (ok === true ? 'ok  ' : ok === false ? 'FAIL' : '--  ')
  return checks.map(c => `${mark(c.ok)} ${c.label}: ${c.detail}`).join('\n')
}

// ---------------------------------------------------------------- main

function readStdin() {
  if (process.stdin.isTTY) return ''
  try {
    return readFileSync(0, 'utf8')
  } catch {
    return ''
  }
}

export function main(argv = process.argv.slice(2)) {
  let opts
  try {
    opts = parseArgs(argv)
  } catch (err) {
    process.stderr.write(`${err.message}\n\n${USAGE}\n`)
    return 2
  }
  if (opts.help) return process.stdout.write(`${USAGE}\n`), 0
  if (opts.version) return process.stdout.write(`${VERSION}\n`), 0

  if (opts.doctor) {
    const checks = doctor()
    const bad = checks.filter(c => c.ok === false).length
    process.stdout.write(opts.json ? `${JSON.stringify({ ok: bad === 0, checks }, null, 2)}\n` : `${formatChecks(checks)}\n${bad ? `\n${bad} problem(s).` : '\nAll good.'}\n`)
    return bad ? 1 : 0
  }

  const usage = message => (process.stderr.write(`${message}\n`), 2)
  const title = cleanTitle(opts.title)
  if (!title) return usage('--title is required. Run with --help for usage.')
  if (title.length > MAX_TITLE) return usage(`--title is ${title.length} characters; keep it to ${MAX_TITLE}.`)

  let raw
  if (opts.file) {
    if (!isFile(opts.file)) return usage(`--file ${opts.file} does not exist.`)
    raw = readFileSync(opts.file, 'utf8')
  } else raw = readStdin()
  const { source, hint } = stripFences(raw)
  if (!source) return usage('No diagram source: pipe it on stdin or pass --file.')

  const language = languageFrom({ flag: opts.language?.toLowerCase(), file: opts.file, hint, source })
  if (!language) return usage(`--language must be one of ${LANGUAGES.join(', ')}.`)
  const theme = (opts.theme || process.env.WHITEBOARD_THEME || 'default').toLowerCase()
  if (!THEMES.includes(theme)) return usage(`--theme must be one of ${THEMES.join(', ')}.`)
  const mermaidConfig = opts.config || process.env.WHITEBOARD_MERMAID_CONFIG || ''
  if (mermaidConfig && !isFile(mermaidConfig)) return usage(`Mermaid config ${mermaidConfig} does not exist.`)

  const report = result => {
    if (opts.json) process.stdout.write(`${JSON.stringify(result, null, 2)}\n`)
    return result
  }

  const r = RENDERERS[language]
  const blocked = allowIncludes() ? null : unsafeDirective(language, source)
  if (blocked) {
    const message = `\`${blocked}\` reads files, environment variables or URLs into the diagram, so it is blocked. ` +
      'Inline the content instead, or set WHITEBOARD_ALLOW_INCLUDES=1 if the user wants includes.'
    report({ ok: false, kind: 'blocked', language, message })
    if (!opts.json) process.stderr.write(`Render refused (${r.label}): ${message}\n`)
    return 1
  }

  const found = findRenderer(language)
  if (!found.path) {
    report({ ok: false, kind: 'missing', language, message: found.error })
    if (!opts.json) process.stderr.write(`${found.error}\n`)
    return 3
  }

  const work = mkdtempSync(join(tmpdir(), 'whiteboard-'))
  try {
    const svg = renderTo(language, found, source, { dir: work, format: 'svg', theme, mermaidConfig })
    if (!svg.ok) {
      report({ ok: false, kind: svg.kind, language, message: svg.message })
      if (!opts.json) process.stderr.write(`Render failed (${svg.kind}, ${r.label}):\n${svg.message}\n\nFix the source and run again.\n`)
      return 1
    }
    if (opts.check) {
      report({ ok: true, language, checked: true })
      if (!opts.json) process.stdout.write(`OK: the ${r.label} source renders. Nothing was written (--check).\n`)
      return 0
    }
    const rendered = { svg: svg.path }
    let pngNote = ''
    if (opts.png && language === 'd2' && hasD2External(source) && !allowIncludes()) {
      pngNote = 'PNG skipped: D2 would fetch or read its images, icons or links into the PNG. The SVG keeps them as links; set WHITEBOARD_ALLOW_INCLUDES=1 for a PNG.'
    } else if (opts.png) {
      const pngDir = join(work, 'png')
      mkdirSync(pngDir)
      const png = renderTo(language, found, source, { dir: pngDir, format: 'png', theme, mermaidConfig })
      if (png.ok) rendered.png = png.path
      else pngNote = `PNG failed: ${png.message}`
    }
    const outDir = resolve(opts.out ?? 'diagrams')
    const name = slug(title)
    let saved
    try {
      saved = save({ outDir, name, ext: r.ext, source, sourceFile: opts.file, rendered })
    } catch (err) {
      if (!(err instanceof UnsafePathError)) throw err
      report({ ok: false, kind: 'unsafe-path', language, message: err.message })
      if (!opts.json) process.stderr.write(`${err.message}\n`)
      return 2
    }
    const { written, version } = saved
    if (opts.open) openFile(written.svg)
    let share
    if (opts.share) share = shareGist(title, language, source, work)

    const rel = p => relative(process.cwd(), p) || p
    report({ ok: true, title, language, version, files: Object.fromEntries(Object.entries(written).map(([k, v]) => [k, rel(v)])), share, warning: pngNote || undefined })
    if (!opts.json) {
      const lines = [`Rendered "${title}" (${r.label}${version > 1 ? `, version ${version}` : ''})`]
      for (const [kind, path] of Object.entries(written)) lines.push(`  ${kind.padEnd(6)} ${rel(path)}`)
      if (pngNote) lines.push(pngNote)
      if (share) lines.push(share.ok ? `Secret gist: ${share.url}` : `Share failed: ${share.message}`)
      process.stdout.write(`${lines.join('\n')}\n`)
    }
    return 0
  } finally {
    rmSync(work, { recursive: true, force: true })
  }
}

const invoked = process.argv[1] && import.meta.url === pathToFileURL(resolve(process.argv[1])).href
if (invoked) process.exitCode = main()
