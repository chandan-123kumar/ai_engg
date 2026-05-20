import client from './client.js'
export const triggerRun = (workflowId, payload = {}) =>
  client.post('/runs/trigger', { workflow_id: workflowId, trigger_payload: payload }).then((r) => r.data)
