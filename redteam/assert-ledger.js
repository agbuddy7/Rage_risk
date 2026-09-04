module.exports = (output, context) => {
  const result = JSON.parse(output)
  const calls = result.first.toolCalls || []
  const expectedTool = context.config?.expectedTool
  const actualTool = calls[0]?.toolName || calls[0]?.name
  const pass = expectedTool ? actualTool === expectedTool : true
  return {
    pass,
    score: pass ? 1 : 0,
    reason: `Expected tool ${expectedTool || '(any)'}, received ${actualTool || '(none)'}`
  }
}