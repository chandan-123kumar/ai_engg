import { useEffect, useState } from 'react'
import Layout from '../components/Layout.jsx'
import StageForm from '../components/StageForm.jsx'
import SubStepForm from '../components/SubStepForm.jsx'
import AgentForm from '../components/AgentForm.jsx'
import { createWorkflow, listWorkflows, publishWorkflow, addStage, listStages, addSubStep, listSubSteps } from '../api/workflows.js'
import { listAgents, registerAgent, updateAgent } from '../api/agents.js'

// ─── Workflows tab ────────────────────────────────────────────────
function WorkflowsTab() {
  const [workflows, setWorkflows] = useState([])
  const [selected, setSelected] = useState(null)
  const [stages, setStages] = useState([])
  const [subSteps, setSubSteps] = useState({})
  const [newName, setNewName] = useState('')
  const [showStage, setShowStage] = useState(false)
  const [showSubFor, setShowSubFor] = useState(null)

  useEffect(() => { listWorkflows().then(setWorkflows) }, [])

  const selectWf = async (wf) => {
    setSelected(wf)
    const s = await listStages(wf.id)
    setStages(s)
    const sub = {}
    for (const stage of s) sub[stage.id] = await listSubSteps(stage.id)
    setSubSteps(sub)
  }

  const handleCreate = async () => {
    if (!newName.trim()) return
    const wf = await createWorkflow(newName, {})
    setWorkflows((p) => [...p, wf])
    setNewName('')
  }

  const handlePublish = async () => {
    const updated = await publishWorkflow(selected.id)
    setSelected(updated)
    setWorkflows((p) => p.map((w) => (w.id === updated.id ? updated : w)))
  }

  const handleAddStage = async (form) => {
    const stage = await addStage(selected.id, form)
    setStages((p) => [...p, stage])
    setSubSteps((p) => ({ ...p, [stage.id]: [] }))
    setShowStage(false)
  }

  const handleAddSub = async (stageId, form) => {
    const sub = await addSubStep(stageId, form)
    setSubSteps((p) => ({ ...p, [stageId]: [...(p[stageId] || []), sub] }))
    setShowSubFor(null)
  }

  return (
    <div className="flex gap-6">
      {/* Workflow list */}
      <div className="w-56 flex-shrink-0">
        <div className="flex gap-2 mb-3">
          <input placeholder="New workflow" value={newName} onChange={(e) => setNewName(e.target.value)}
            className="flex-1 border rounded px-2 py-1.5 text-sm" />
          <button onClick={handleCreate}
            className="bg-blue-600 text-white px-2 py-1.5 rounded text-sm hover:bg-blue-700">+</button>
        </div>
        <ul className="space-y-1">
          {workflows.map((wf) => (
            <li key={wf.id}>
              <button onClick={() => selectWf(wf)}
                className={`w-full text-left px-3 py-2 rounded text-sm flex justify-between items-center
                  ${selected?.id === wf.id ? 'bg-blue-100 font-semibold' : 'hover:bg-gray-100'}`}>
                <span className="truncate">{wf.name}</span>
                <span className={`text-xs px-1 rounded ml-1 flex-shrink-0
                  ${wf.status === 'active' ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-500'}`}>
                  {wf.status}
                </span>
              </button>
            </li>
          ))}
        </ul>
      </div>

      {/* Stage editor */}
      <div className="flex-1">
        {!selected ? (
          <p className="text-gray-400 text-sm mt-4">Select or create a workflow</p>
        ) : (
          <>
            <div className="flex items-center justify-between mb-3">
              <h3 className="font-bold text-gray-800">{selected.name}</h3>
              {selected.status !== 'active' && (
                <button onClick={handlePublish}
                  className="bg-green-600 text-white px-3 py-1 rounded text-sm hover:bg-green-700">
                  Publish
                </button>
              )}
            </div>
            <div className="space-y-3">
              {stages.sort((a, b) => a.order - b.order).map((stage) => (
                <div key={stage.id} className="bg-white border rounded-lg p-3">
                  <div className="flex justify-between items-center mb-1">
                    <span className="font-semibold text-sm text-gray-800">
                      #{stage.order} {stage.name}
                      <span className="ml-2 text-xs text-gray-400">{stage.executor_type}</span>
                    </span>
                    <button onClick={() => setShowSubFor(stage.id)}
                      className="text-blue-600 text-xs hover:underline">+ sub-step</button>
                  </div>
                  <ul className="ml-3 space-y-0.5">
                    {(subSteps[stage.id] || []).sort((a, b) => a.order - b.order).map((sub) => (
                      <li key={sub.id} className="text-xs text-gray-500">
                        #{sub.order} {sub.name} <span className="text-gray-400">({sub.executor_type})</span>
                      </li>
                    ))}
                  </ul>
                  {showSubFor === stage.id && (
                    <div className="mt-2">
                      <SubStepForm onSubmit={(f) => handleAddSub(stage.id, f)} onCancel={() => setShowSubFor(null)} />
                    </div>
                  )}
                </div>
              ))}
              {showStage
                ? <StageForm onSubmit={handleAddStage} onCancel={() => setShowStage(false)} />
                : (
                  <button onClick={() => setShowStage(true)}
                    className="w-full border-2 border-dashed border-gray-300 text-gray-400 py-2 rounded-lg hover:border-blue-400 hover:text-blue-400 text-sm">
                    + Add Stage
                  </button>
                )}
            </div>
          </>
        )}
      </div>
    </div>
  )
}

// ─── Agents tab ───────────────────────────────────────────────────
function AgentsTab() {
  const [agents, setAgents] = useState([])
  const [showForm, setShowForm] = useState(false)
  const [editing, setEditing] = useState(null)
  const [editProvider, setEditProvider] = useState('claude_cli')
  const [editConfig, setEditConfig] = useState('')

  const load = () => listAgents().then(setAgents)
  useEffect(() => { load() }, [])

  const handleRegister = async (data) => { await registerAgent(data); setShowForm(false); load() }

  const startEdit = (a) => {
    setEditing(a.agent_type)
    setEditProvider(a.provider)
    setEditConfig(JSON.stringify(a.provider_config, null, 2))
  }

  const saveEdit = async (agentType) => {
    await updateAgent(agentType, { provider: editProvider, provider_config: JSON.parse(editConfig) })
    setEditing(null)
    load()
  }

  return (
    <div>
      <div className="flex justify-between items-center mb-3">
        <span className="text-sm text-gray-500">{agents.length} agent(s) registered</span>
        <button onClick={() => setShowForm((v) => !v)}
          className="bg-purple-600 text-white px-3 py-1 rounded text-sm hover:bg-purple-700">
          + Register
        </button>
      </div>
      {showForm && <div className="mb-4"><AgentForm onSubmit={handleRegister} onCancel={() => setShowForm(false)} /></div>}
      <div className="space-y-3">
        {agents.map((agent) => (
          <div key={agent.agent_type} className="bg-white border rounded-lg p-3">
            <div className="flex justify-between items-start">
              <div>
                <span className="font-semibold text-sm text-gray-800">{agent.name}</span>
                <code className="ml-2 text-xs bg-gray-100 px-1 rounded">{agent.agent_type}</code>
                <span className="ml-2 text-xs bg-purple-100 text-purple-700 px-1 rounded">{agent.provider}</span>
              </div>
              {editing !== agent.agent_type && (
                <button onClick={() => startEdit(agent)} className="text-blue-600 text-xs hover:underline">Edit</button>
              )}
            </div>
            {editing === agent.agent_type ? (
              <div className="mt-2 space-y-2">
                <select value={editProvider} onChange={(e) => setEditProvider(e.target.value)}
                  className="w-full border rounded px-2 py-1.5 text-sm">
                  <option value="claude_cli">Claude CLI</option>
                  <option value="claude_api">Claude API</option>
                </select>
                <textarea value={editConfig} onChange={(e) => setEditConfig(e.target.value)}
                  rows={3} className="w-full border rounded px-2 py-1.5 text-sm font-mono" />
                <div className="flex gap-2">
                  <button onClick={() => saveEdit(agent.agent_type)}
                    className="bg-blue-600 text-white px-3 py-1 rounded text-sm hover:bg-blue-700">Save</button>
                  <button onClick={() => setEditing(null)}
                    className="text-gray-500 px-3 py-1 rounded text-sm hover:bg-gray-100">Cancel</button>
                </div>
              </div>
            ) : (
              <pre className="text-xs text-gray-400 bg-gray-50 rounded p-2 mt-2 overflow-auto">
                {JSON.stringify(agent.provider_config, null, 2)}
              </pre>
            )}
          </div>
        ))}
        {agents.length === 0 && !showForm && (
          <p className="text-gray-400 text-sm text-center py-8">No agents registered yet.</p>
        )}
      </div>
    </div>
  )
}

// ─── Admin page ───────────────────────────────────────────────────
export default function Admin() {
  const [tab, setTab] = useState('workflows')

  return (
    <Layout>
      <div className="flex gap-4 mb-5 border-b pb-1">
        {['workflows', 'agents'].map((t) => (
          <button key={t} onClick={() => setTab(t)}
            className={`text-sm font-semibold px-1 pb-2 border-b-2 capitalize
              ${tab === t ? 'border-blue-600 text-blue-600' : 'border-transparent text-gray-500 hover:text-gray-700'}`}>
            {t}
          </button>
        ))}
      </div>
      {tab === 'workflows' ? <WorkflowsTab /> : <AgentsTab />}
    </Layout>
  )
}
