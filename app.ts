/*
 * Copyright (c) 2014-2026 Bjoern Kimminich & the OWASP Juice Shop contributors.
 * SPDX-License-Identifier: MIT
 */

import fs from 'fs'
import path from 'path'

// Auto-load .env file if present
try {
  if (typeof (process as any).loadEnvFile === 'function') {
    const envFile = path.join(process.cwd(), '.env')
    if (fs.existsSync(envFile)) {
      (process as any).loadEnvFile(envFile)
    }
  } else {
    const envFile = path.join(process.cwd(), '.env')
    if (fs.existsSync(envFile)) {
      const content = fs.readFileSync(envFile, 'utf8')
      content.split('\n').forEach(line => {
        const trimmed = line.trim()
        if (trimmed && !trimmed.startsWith('#') && trimmed.includes('=')) {
          const idx = trimmed.indexOf('=')
          const key = trimmed.slice(0, idx).trim()
          const val = trimmed.slice(idx + 1).trim().replace(/^['"]|['"]$/g, '')
          if (key && !process.env[key]) process.env[key] = val
        }
      })
    }
  }
} catch {
  // ignore
}

async function app () {
  const { default: validateDependencies } = await import('./lib/startup/validateDependenciesBasic')
  await validateDependencies()

  const server = await import('./server')
  await server.start()
}

app()
  .catch(err => {
    throw err
  })
