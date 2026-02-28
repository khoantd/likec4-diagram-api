#!/usr/bin/env node
/**
 * parse-c4.mjs – Validate LikeC4 DSL source from stdin using @likec4/language-services.
 *
 * Usage:
 *   echo 'model { }' | node parse-c4.mjs
 *
 * Output (stdout, JSON):
 *   { "valid": true }
 *   { "valid": false, "errors": [{ "message", "line", "sourceFsPath", "range" }] }
 *
 * Exit codes:
 *   0 – valid or invalid DSL (check the JSON "valid" field)
 *   1 – runtime error (stdin read failure, module import failure, etc.)
 */

import { createInterface } from 'node:readline'

async function readStdin() {
  const chunks = []
  const rl = createInterface({ input: process.stdin, crlfDelay: Infinity })
  for await (const line of rl) {
    chunks.push(line)
  }
  return chunks.join('\n')
}

async function main() {
  let source
  try {
    source = await readStdin()
  } catch (err) {
    process.stderr.write(`parse-c4: failed to read stdin: ${err.message}\n`)
    process.exit(1)
  }

  let fromSource
  try {
    // Try the without-mcp build first (lighter), fall back to the full build
    try {
      const mod = await import('@likec4/language-services/node/without-mcp')
      fromSource = mod.fromSource
    } catch {
      const mod = await import('@likec4/language-services/node')
      fromSource = mod.fromSource
    }
  } catch (err) {
    process.stderr.write(`parse-c4: failed to import @likec4/language-services: ${err.message}\n`)
    process.exit(1)
  }

  let likec4
  try {
    likec4 = await fromSource(source)
  } catch (err) {
    // Catastrophic parse error (should rarely happen; most errors surface via getErrors())
    const result = {
      valid: false,
      errors: [{ message: String(err.message ?? err), line: 0, sourceFsPath: 'source.c4', range: null }],
    }
    process.stdout.write(JSON.stringify(result) + '\n')
    return
  }

  const errors = likec4.getErrors()
  if (errors.length === 0) {
    process.stdout.write(JSON.stringify({ valid: true }) + '\n')
  } else {
    process.stdout.write(JSON.stringify({ valid: false, errors }) + '\n')
  }
}

main().catch(err => {
  process.stderr.write(`parse-c4: unexpected error: ${err.message}\n`)
  process.exit(1)
})
