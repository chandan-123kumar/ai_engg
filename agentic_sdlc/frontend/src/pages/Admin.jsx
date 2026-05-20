import { useEffect, useState, useCallback } from 'react'
import {
  DndContext, closestCenter, PointerSensor, useSensor, useSensors,
} from '@dnd-kit/core'
import {
  SortableContext, useSortable, verticalListSortingStrategy, arrayMove,
} from '@dnd-kit/sortable'
import { CSS } from '@dnd-kit/utilities'
import Layout from '../components/Layout.jsx'
import StageForm from '../components/StageForm.jsx'
import SubStepForm from '../components/SubStepForm.jsx'
import AgentForm from '../components/AgentForm.jsx'
import {
  createWorkflow, listWorkflows, publishWorkflow,
  addStage, listStages, addSubStep, listSubSteps, updateStage, updateSubStep,
} from '../api/workflows.js'
import { listAgents, registerAgent, updateAgent } from '../api/agents.js'

// ─── Drag handle ─────────────────────────────────────────────────
function DragHandle({ listeners, attributes }) {
  return (
    <span {...listeners} {...attributes}
      className="cursor-grab active:cursor-grabbing text-gray-300 hover:text-gray-500 select-none px-1 text-base leading-none"
      title="Drag to reorder">
      ⠿
    </span>
  )
}

// ─── Sortable stage card ──────────────────────────────────────────
function SortableStageCard({ stage, children }) {
  const { attributes, listeners, setNodeRef, transform, transition, isDragging } = useSortable({ id: stage.id })
  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
    opacity: isDragging ? 0.4 : 1,
  }
  return (
    <div ref={setNodeRef} style={style} className="bg-white border rounded-lg p-3">
      {children({ dragHandle: <DragHandle listeners={listeners} attributes={attributes} /> })}
    </div>
  )
}

// ─── Sortable sub-step row ────────────────────────────────────────
function SortableSubRow({ sub, children }) {
  const { attributes, listeners, setNodeRef, transform, transition, isDragging } = useSortable({ id: sub.id })
  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
    opacity: isDragging ? 0.4 : 1,
  }
  return (
    <li ref={setNodeRef} style={style}>
      {children({ dragHandle: <DragHandle listeners={listeners} attributes={attributes} /> })}
    </li>
  )
}

// ─── Workflow diagram ─────────────────────────────────────────────
const GATE_COLORS = {
  none: 'border-blue-400 bg-blue-50',
  github_pr: 'border-purple-400 bg-purple-50',
  slack: 'border-green-400 bg-green-50',
  email: 'border-orange-400 bg-orange-50',
}
const GATE_LABEL = { none: '', github_pr: 'PR', slack: 'Slack', email: 'Email' }

function WorkflowDiagram({ stages, subSteps, agents }) {
  const sorted = [...stages].sort((a, b) => a.order - b.order)
  const agentName = (t) => { const a = agents.find((x) => x.agent_type === t); return a ? a.name : t }

  if (sorted.length === 0) {
    return (
      <div className="flex items-center justify-center h-full text-gray-300 text-sm">
        Add a stage to see the diagram
      </div>
    )
  }

  return (
    <div className="flex flex-col items-center py-4 overflow-y-auto h-full">
      {sorted.map((stage, i) => (
        <div key={stage.id} className="flex flex-col items-center w-full">
          <div className={`w-52 border-2 rounded-lg px-3 py-2 shadow-sm ${GATE_COLORS[stage.gate_type] || 'border-blue-400 bg-blue-50'}`}>
            <div className="flex justify-between items-center">
              <span className="font-semibold text-xs text-gray-700 truncate">#{stage.order} {stage.name}</span>
              {GATE_LABEL[stage.gate_type] && (
                <span className="text-xs bg-white border rounded px-1 text-gray-500">{GATE_LABEL[stage.gate_type]}</span>
              )}
            </div>
            <div className="text-xs text-gray-400 mt-0.5 flex items-center gap-1">
              {stage.executor_type}
              {stage.config?.agent_type && (
                <span className="bg-indigo-100 text-indigo-700 px-1 rounded">{agentName(stage.config.agent_type)}</span>
              )}
            </div>
            {(subSteps[stage.id] || []).length > 0 && (
              <ul className="mt-1 space-y-0.5">
                {[...(subSteps[stage.id] || [])].sort((a, b) => a.order - b.order).map((sub) => {
                  const parts = sub.agent_conversation_config?.participants || []
                  return (
                    <li key={sub.id} className="text-xs bg-white rounded px-1.5 py-0.5 text-gray-600 truncate">
                      ↳ {sub.name}
                      {parts.length > 0 && (
                        <span className="ml-1 text-indigo-500">[{parts.map(agentName).join(', ')}]</span>
                      )}
                    </li>
                  )
                })}
              </ul>
            )}
          </div>
          {i < sorted.length - 1 && (
            <div className="flex flex-col items-center my-0.5">
              <div className="w-px h-4 bg-gray-300" />
              <div className="w-0 h-0 border-l-4 border-r-4 border-t-4 border-l-transparent border-r-transparent border-t-gray-300" />
            </div>
          )}
        </div>
      ))}
    </div>
  )
}

// ─── Sub-step edit form (inline) ──────────────────────────────────
function SubEditForm({ sub, agents, onSave, onCancel }) {
  const acc = sub.agent_conversation_config || {}
  const [sf, setSf] = useState({
    name: sub.name,
    order: sub.order,
    executor_type: sub.executor_type,
    participants: acc.participants || [],
    initiator: acc.initiator || '',
    condition: acc.termination?.condition || 'single_turn',
  })
  const set = (k, v) => setSf((f) => ({ ...f, [k]: v }))

  const toggleP = (agentType) => {
    const next = sf.participants.includes(agentType)
      ? sf.participants.filter((p) => p !== agentType)
      : [...sf.participants, agentType]
    setSf((f) => ({ ...f, participants: next, initiator: next.includes(f.initiator) ? f.initiator : next[0] || '' }))
  }

  const handleSave = () => {
    const agent_conversation_config = {
      ...acc,
      participants: sf.participants,
      initiator: sf.initiator || sf.participants[0] || '',
      termination: { condition: sf.condition },
    }
    onSave({ name: sf.name, order: sf.order, executor_type: sf.executor_type, agent_conversation_config })
  }

  return (
    <div className="bg-blue-50 border border-blue-200 rounded p-2 space-y-1.5">
      <input value={sf.name} onChange={(e) => set('name', e.target.value)}
        className="w-full border rounded px-2 py-1 text-xs" />
      <div className="flex gap-1.5">
        <input type="number" value={sf.order} onChange={(e) => set('order', Number(e.target.value))}
          className="w-16 border rounded px-2 py-1 text-xs" />
        <select value={sf.executor_type} onChange={(e) => set('executor_type', e.target.value)}
          className="flex-1 border rounded px-2 py-1 text-xs">
          <option value="agent">Agent</option>
          <option value="human">Human</option>
        </select>
        <select value={sf.condition} onChange={(e) => set('condition', e.target.value)}
          className="flex-1 border rounded px-2 py-1 text-xs">
          <option value="single_turn">Single turn</option>
          <option value="reviewer_approves">Reviewer approves</option>
          <option value="max_turns">Max turns</option>
          <option value="tool_success">Tool success</option>
        </select>
      </div>
      {sf.executor_type === 'agent' && (
        <div>
          <p className="text-xs text-gray-500 mb-0.5">Participants</p>
          {agents.length === 0
            ? <p className="text-xs text-gray-400 italic">No agents registered</p>
            : (
              <div className="flex flex-wrap gap-1">
                {agents.map((a) => {
                  const sel = sf.participants.includes(a.agent_type)
                  return (
                    <button key={a.agent_type} type="button" onClick={() => toggleP(a.agent_type)}
                      className={`text-xs px-1.5 py-0.5 rounded border transition-colors
                        ${sel ? 'bg-blue-600 text-white border-blue-600' : 'bg-white text-gray-600 border-gray-300 hover:border-blue-400'}`}>
                      {a.name}
                    </button>
                  )
                })}
              </div>
            )}
          {sf.participants.length > 1 && (
            <select value={sf.initiator} onChange={(e) => set('initiator', e.target.value)}
              className="w-full border rounded px-2 py-1 text-xs mt-1">
              {sf.participants.map((p) => {
                const a = agents.find((x) => x.agent_type === p)
                return <option key={p} value={p}>{a ? a.name : p}</option>
              })}
            </select>
          )}
        </div>
      )}
      <div className="flex gap-1.5">
        <button onClick={handleSave}
          className="bg-blue-600 text-white px-2 py-0.5 rounded text-xs hover:bg-blue-700">Save</button>
        <button onClick={onCancel}
          className="text-gray-500 px-2 py-0.5 rounded text-xs hover:bg-gray-100">Cancel</button>
      </div>
    </div>
  )
}

// ─── Workflows tab ────────────────────────────────────────────────
function WorkflowsTab() {
  const [workflows, setWorkflows] = useState([])
  const [agents, setAgents] = useState([])
  const [selected, setSelected] = useState(null)
  const [stages, setStages] = useState([])
  const [subSteps, setSubSteps] = useState({})
  const [newName, setNewName] = useState('')
  const [showStage, setShowStage] = useState(false)
  const [showSubFor, setShowSubFor] = useState(null)
  const [editingStage, setEditingStage] = useState(null)
  const [stageEditFields, setStageEditFields] = useState({})
  const [editingSub, setEditingSub] = useState(null)

  const sensors = useSensors(useSensor(PointerSensor, { activationConstraint: { distance: 5 } }))

  useEffect(() => {
    listWorkflows().then(setWorkflows)
    listAgents().then(setAgents)
  }, [])

  const selectWf = async (wf) => {
    setSelected(wf)
    setShowStage(false)
    setShowSubFor(null)
    setEditingStage(null)
    setEditingSub(null)
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

  // ── Stage drag end ───────────────────────────────────────────────
  const handleStageDragEnd = useCallback(async ({ active, over }) => {
    if (!over || active.id === over.id) return
    const sorted = [...stages].sort((a, b) => a.order - b.order)
    const oldIdx = sorted.findIndex((s) => s.id === active.id)
    const newIdx = sorted.findIndex((s) => s.id === over.id)
    const reordered = arrayMove(sorted, oldIdx, newIdx)
    // Optimistic update
    const updated = reordered.map((s, i) => ({ ...s, order: i + 1 }))
    setStages(updated)
    // Persist only changed
    await Promise.all(
      updated
        .filter((s, i) => sorted[i]?.id !== s.id || s.order !== sorted.find((x) => x.id === s.id)?.order)
        .map((s) => updateStage(s.id, { order: s.order }))
    )
  }, [stages])

  // ── Sub-step drag end ────────────────────────────────────────────
  const handleSubDragEnd = useCallback(async (stageId, { active, over }) => {
    if (!over || active.id === over.id) return
    const sorted = [...(subSteps[stageId] || [])].sort((a, b) => a.order - b.order)
    const oldIdx = sorted.findIndex((s) => s.id === active.id)
    const newIdx = sorted.findIndex((s) => s.id === over.id)
    const reordered = arrayMove(sorted, oldIdx, newIdx)
    const updated = reordered.map((s, i) => ({ ...s, order: i + 1 }))
    setSubSteps((p) => ({ ...p, [stageId]: updated }))
    await Promise.all(
      updated
        .filter((s, i) => sorted[i]?.id !== s.id || s.order !== sorted.find((x) => x.id === s.id)?.order)
        .map((s) => updateSubStep(s.id, { order: s.order }))
    )
  }, [subSteps])

  // ── Stage edit ───────────────────────────────────────────────────
  const startEditStage = (stage) => {
    setEditingStage(stage.id)
    setStageEditFields({
      name: stage.name,
      order: stage.order,
      executor_type: stage.executor_type,
      gate_type: stage.gate_type || 'none',
      agent_type: stage.config?.agent_type || '',
    })
  }

  const saveStageEdit = async (stageId) => {
    const { agent_type, ...rest } = stageEditFields
    const config = agent_type ? { agent_type } : {}
    const updated = await updateStage(stageId, { ...rest, config })
    setStages((p) => p.map((s) => (s.id === stageId ? updated : s)))
    setEditingStage(null)
  }

  // ── Sub-step edit ────────────────────────────────────────────────
  const saveSubEdit = async (sub, data) => {
    const updated = await updateSubStep(sub.id, data)
    setSubSteps((p) => ({
      ...p,
      [sub.stage_id]: (p[sub.stage_id] || []).map((s) => (s.id === sub.id ? updated : s)),
    }))
    setEditingSub(null)
  }

  const handleAddSub = async (stageId, form) => {
    const sub = await addSubStep(stageId, form)
    setSubSteps((p) => ({ ...p, [stageId]: [...(p[stageId] || []), sub] }))
    setShowSubFor(null)
  }

  const sortedStages = [...stages].sort((a, b) => a.order - b.order)

  return (
    <div className="flex gap-4 h-full">
      {/* Workflow list */}
      <div className="w-48 flex-shrink-0">
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

      {!selected ? (
        <p className="text-gray-400 text-sm mt-4 flex-1">Select or create a workflow</p>
      ) : (
        <>
          {/* Stage editor */}
          <div className="flex-1 min-w-0 overflow-y-auto">
            <div className="flex items-center justify-between mb-3">
              <h3 className="font-bold text-gray-800">{selected.name}</h3>
              {selected.status !== 'active' && (
                <button onClick={handlePublish}
                  className="bg-green-600 text-white px-3 py-1 rounded text-sm hover:bg-green-700">
                  Publish
                </button>
              )}
            </div>

            <DndContext sensors={sensors} collisionDetection={closestCenter} onDragEnd={handleStageDragEnd}>
              <SortableContext items={sortedStages.map((s) => s.id)} strategy={verticalListSortingStrategy}>
                <div className="space-y-3">
                  {sortedStages.map((stage) => {
                    const stageAgent = stage.config?.agent_type
                      ? agents.find((a) => a.agent_type === stage.config.agent_type)
                      : null
                    const isEditing = editingStage === stage.id
                    const ef = stageEditFields
                    const setEf = (k, v) => setStageEditFields((f) => ({ ...f, [k]: v }))
                    const sortedSubs = [...(subSteps[stage.id] || [])].sort((a, b) => a.order - b.order)

                    return (
                      <SortableStageCard key={stage.id} stage={stage}>
                        {({ dragHandle }) => (
                          isEditing ? (
                            <div className="space-y-2">
                              <input value={ef.name} onChange={(e) => setEf('name', e.target.value)}
                                placeholder="Stage name" className="w-full border rounded px-2 py-1.5 text-sm" />
                              <div className="flex gap-2">
                                <select value={ef.executor_type} onChange={(e) => setEf('executor_type', e.target.value)}
                                  className="flex-1 border rounded px-2 py-1.5 text-sm">
                                  <option value="agent">Agent</option>
                                  <option value="human">Human</option>
                                </select>
                                <select value={ef.gate_type} onChange={(e) => setEf('gate_type', e.target.value)}
                                  className="flex-1 border rounded px-2 py-1.5 text-sm">
                                  <option value="none">No gate</option>
                                  <option value="github_pr">GitHub PR</option>
                                  <option value="slack">Slack</option>
                                  <option value="email">Email</option>
                                </select>
                              </div>
                              {ef.executor_type === 'agent' && (
                                <select value={ef.agent_type} onChange={(e) => setEf('agent_type', e.target.value)}
                                  className="w-full border rounded px-2 py-1.5 text-sm">
                                  <option value="">— Assign agent —</option>
                                  {agents.map((a) => (
                                    <option key={a.agent_type} value={a.agent_type}>{a.name} ({a.agent_type})</option>
                                  ))}
                                </select>
                              )}
                              <div className="flex gap-2">
                                <button onClick={() => saveStageEdit(stage.id)}
                                  className="bg-blue-600 text-white px-3 py-1 rounded text-sm hover:bg-blue-700">Save</button>
                                <button onClick={() => setEditingStage(null)}
                                  className="text-gray-500 px-3 py-1 rounded text-sm hover:bg-gray-100">Cancel</button>
                              </div>
                            </div>
                          ) : (
                            <>
                              <div className="flex items-center justify-between mb-1">
                                <div className="flex items-center gap-1 min-w-0">
                                  {dragHandle}
                                  <span className="font-semibold text-sm text-gray-800 truncate">{stage.name}</span>
                                  <span className="text-xs text-gray-400 flex-shrink-0">{stage.executor_type}</span>
                                  {stageAgent && (
                                    <span className="text-xs bg-indigo-100 text-indigo-700 px-1.5 rounded flex-shrink-0">
                                      {stageAgent.name}
                                    </span>
                                  )}
                                </div>
                                <div className="flex gap-2 flex-shrink-0 ml-2">
                                  <button onClick={() => startEditStage(stage)}
                                    className="text-gray-400 text-xs hover:text-gray-700">Edit</button>
                                  <button onClick={() => setShowSubFor(showSubFor === stage.id ? null : stage.id)}
                                    className="text-blue-600 text-xs hover:underline">+ sub-step</button>
                                </div>
                              </div>

                              {/* Sub-steps with their own DnD context */}
                              <DndContext
                                sensors={sensors}
                                collisionDetection={closestCenter}
                                onDragEnd={(e) => handleSubDragEnd(stage.id, e)}
                              >
                                <SortableContext items={sortedSubs.map((s) => s.id)} strategy={verticalListSortingStrategy}>
                                  <ul className="ml-4 space-y-1 mt-1">
                                    {sortedSubs.map((sub) => (
                                      <SortableSubRow key={sub.id} sub={sub}>
                                        {({ dragHandle: subHandle }) => (
                                          editingSub === sub.id ? (
                                            <SubEditForm
                                              sub={sub}
                                              agents={agents}
                                              onSave={(data) => saveSubEdit(sub, data)}
                                              onCancel={() => setEditingSub(null)}
                                            />
                                          ) : (
                                            <div className="flex items-center gap-1 text-xs text-gray-500 flex-wrap py-0.5">
                                              {subHandle}
                                              <span className="font-medium text-gray-700">{sub.name}</span>
                                              <span className="text-gray-400">({sub.executor_type})</span>
                                              {(sub.agent_conversation_config?.participants || []).map((p) => {
                                                const pa = agents.find((a) => a.agent_type === p)
                                                return (
                                                  <span key={p} className="bg-indigo-100 text-indigo-700 px-1 rounded">
                                                    {pa ? pa.name : p}
                                                  </span>
                                                )
                                              })}
                                              <button onClick={() => setEditingSub(sub.id)}
                                                className="ml-auto text-gray-400 hover:text-blue-600 text-xs">
                                                Edit
                                              </button>
                                            </div>
                                          )
                                        )}
                                      </SortableSubRow>
                                    ))}
                                  </ul>
                                </SortableContext>
                              </DndContext>

                              {showSubFor === stage.id && (
                                <div className="mt-2">
                                  <SubStepForm agents={agents}
                                    onSubmit={(f) => handleAddSub(stage.id, f)}
                                    onCancel={() => setShowSubFor(null)} />
                                </div>
                              )}
                            </>
                          )
                        )}
                      </SortableStageCard>
                    )
                  })}
                </div>
              </SortableContext>
            </DndContext>

            <div className="mt-3">
              {showStage
                ? <StageForm agents={agents} onSubmit={handleAddStage} onCancel={() => setShowStage(false)} />
                : (
                  <button onClick={() => setShowStage(true)}
                    className="w-full border-2 border-dashed border-gray-300 text-gray-400 py-2 rounded-lg hover:border-blue-400 hover:text-blue-400 text-sm">
                    + Add Stage
                  </button>
                )}
            </div>
          </div>

          {/* Live diagram */}
          <div className="w-64 flex-shrink-0 border-l pl-4">
            <p className="text-xs font-semibold text-gray-400 uppercase tracking-wide mb-3">Flow</p>
            <WorkflowDiagram stages={stages} subSteps={subSteps} agents={agents} />
          </div>
        </>
      )}
    </div>
  )
}

// ─── Agents tab ───────────────────────────────────────────────────
function AgentsTab() {
  const [agents, setAgents] = useState([])
  const [showForm, setShowForm] = useState(false)
  const [editing, setEditing] = useState(null)
  const [editFields, setEditFields] = useState({ name: '', provider: 'claude_cli', provider_config: '' })
  const [editErr, setEditErr] = useState('')

  const load = () => listAgents().then(setAgents)
  useEffect(() => { load() }, [])

  const handleRegister = async (data) => { await registerAgent(data); setShowForm(false); load() }

  const startEdit = (a) => {
    setEditing(a.agent_type)
    setEditFields({ name: a.name, provider: a.provider, provider_config: JSON.stringify(a.provider_config, null, 2) })
    setEditErr('')
  }

  const saveEdit = async (agentType) => {
    let parsed
    try { parsed = JSON.parse(editFields.provider_config) } catch {
      setEditErr('provider_config must be valid JSON'); return
    }
    await updateAgent(agentType, { name: editFields.name, provider: editFields.provider, provider_config: parsed })
    setEditing(null)
    load()
  }

  const setField = (k, v) => setEditFields((f) => ({ ...f, [k]: v }))

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
                <input value={editFields.name} onChange={(e) => setField('name', e.target.value)}
                  placeholder="Display name" className="w-full border rounded px-2 py-1.5 text-sm" />
                <select value={editFields.provider} onChange={(e) => setField('provider', e.target.value)}
                  className="w-full border rounded px-2 py-1.5 text-sm">
                  <option value="claude_cli">Claude CLI</option>
                  <option value="claude_api">Claude API</option>
                </select>
                <textarea value={editFields.provider_config} onChange={(e) => setField('provider_config', e.target.value)}
                  rows={4} placeholder='{"model": "claude-sonnet-4-6"}'
                  className="w-full border rounded px-2 py-1.5 text-sm font-mono" />
                {editErr && <p className="text-red-600 text-xs">{editErr}</p>}
                <div className="flex gap-2">
                  <button onClick={() => saveEdit(agent.agent_type)}
                    className="bg-blue-600 text-white px-3 py-1 rounded text-sm hover:bg-blue-700">Save</button>
                  <button onClick={() => { setEditing(null); setEditErr('') }}
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
