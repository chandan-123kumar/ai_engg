import client from './client.js'
export const registerAgent = (data) =>
  client.post('/agents/registry', data).then((r) => r.data)
export const listAgents = () =>
  client.get('/agents/registry').then((r) => r.data)
export const updateAgent = (agentType, data) =>
  client.patch(`/agents/registry/${agentType}`, data).then((r) => r.data)
