const BASE_URL = process.env.LEDGER_URL || 'http://localhost:3000'

async function callLedger (message, confirmTransfer = false) {
  const response = await fetch(`${BASE_URL}/rest/agentic-banking`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      messages: [{ role: 'user', content: message }],
      confirmTransfer
    })
  })
  const body = await response.json()
  if (!response.ok) throw new Error(body.error || `Ledger returned HTTP ${response.status}`)
  return body
}

class LedgerProvider {
  id () {
    return 'ledger-agent'
  }

  async callApi (prompt, context) {
    const first = await callLedger(prompt)
    let final = first
    if (context.vars?.confirm === true && first.text?.includes('confirm')) {
      final = await callLedger('yes', true)
    }
    return {
      output: JSON.stringify({ first, final }),
      metadata: { first, final }
    }
  }
}

module.exports = LedgerProvider