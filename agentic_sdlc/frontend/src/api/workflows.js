import client from './client.js'
export const createWorkflow = (name, trigger) =>
  client.post('/workflows', { name, trigger }).then((r) => r.data)
export const listWorkflows = () =>
  client.get('/workflows').then((r) => r.data)
export const publishWorkflow = (id) =>
  client.post(`/workflows/${id}/publish`).then((r) => r.data)
export const addStage = (workflowId, stage) =>
  client.post(`/workflows/${workflowId}/stages`, stage).then((r) => r.data)
export const listStages = (workflowId) =>
  client.get(`/workflows/${workflowId}/stages`).then((r) => r.data)
export const addSubStep = (stageId, substep) =>
  client.post(`/stages/${stageId}/substeps`, substep).then((r) => r.data)
export const listSubSteps = (stageId) =>
  client.get(`/stages/${stageId}/substeps`).then((r) => r.data)
export const updateStage = (stageId, data) =>
  client.patch(`/stages/${stageId}`, data).then((r) => r.data)
export const updateSubStep = (substepId, data) =>
  client.patch(`/substeps/${substepId}`, data).then((r) => r.data)
