import { useState } from 'react'

export default function SubStepForm({ onSubmit, onCancel, agents = [] }) {
  const [form, setForm] = useState({
    name: '', order: 1, executor_type: 'agent',
    agent_conversation_config: {
      participants: [],
      initiator: '',
      termination: { condition: 'single_turn', max_turns: 1 },
    },
    on_complete: 'next_step', on_reject: 'halt',
  })
  const set = (k, v) => setForm((f) => ({ ...f, [k]: v }))

  const acc = form.agent_conversation_config
  const setAcc = (patch) => set('agent_conversation_config', { ...acc, ...patch })
  const setCondition = (condition) => setAcc({ termination: { ...acc.termination, condition } })

  const toggleParticipant = (agentType) => {
    const next = acc.participants.includes(agentType)
      ? acc.participants.filter((p) => p !== agentType)
      : [...acc.participants, agentType]
    setAcc({ participants: next, initiator: next[0] || '' })
  }

  return (
    <div className="bg-blue-50 border border-blue-200 rounded p-3 space-y-2 ml-4">
      <p className="text-xs font-semibold text-gray-600">New Sub-Step</p>
      <input placeholder="Sub-step name" value={form.name} onChange={(e) => set('name', e.target.value)}
        className="w-full border rounded px-2 py-1.5 text-sm" />
      <div className="flex gap-2">
        <input type="number" placeholder="Order" value={form.order}
          onChange={(e) => set('order', Number(e.target.value))}
          className="w-20 border rounded px-2 py-1.5 text-sm" />
        <select value={form.executor_type} onChange={(e) => set('executor_type', e.target.value)}
          className="flex-1 border rounded px-2 py-1.5 text-sm">
          <option value="agent">Agent</option>
          <option value="human">Human</option>
        </select>
        <select value={acc.termination.condition} onChange={(e) => setCondition(e.target.value)}
          className="flex-1 border rounded px-2 py-1.5 text-sm">
          <option value="single_turn">Single turn</option>
          <option value="reviewer_approves">Reviewer approves</option>
          <option value="max_turns">Max turns</option>
          <option value="tool_success">Tool success</option>
        </select>
      </div>

      {form.executor_type === 'agent' && (
        <div className="space-y-1">
          <p className="text-xs text-gray-500 font-medium">Participants</p>
          {agents.length === 0 && (
            <p className="text-xs text-gray-400 italic">No agents registered yet</p>
          )}
          <div className="flex flex-wrap gap-1">
            {agents.map((a) => {
              const selected = acc.participants.includes(a.agent_type)
              return (
                <button key={a.agent_type} type="button" onClick={() => toggleParticipant(a.agent_type)}
                  className={`text-xs px-2 py-1 rounded border transition-colors
                    ${selected ? 'bg-blue-600 text-white border-blue-600' : 'bg-white text-gray-600 border-gray-300 hover:border-blue-400'}`}>
                  {a.name}
                </button>
              )
            })}
          </div>
          {acc.participants.length > 1 && (
            <div>
              <p className="text-xs text-gray-500 font-medium mt-1">Initiator</p>
              <select value={acc.initiator} onChange={(e) => setAcc({ initiator: e.target.value })}
                className="w-full border rounded px-2 py-1.5 text-sm">
                {acc.participants.map((p) => {
                  const agent = agents.find((a) => a.agent_type === p)
                  return <option key={p} value={p}>{agent ? agent.name : p}</option>
                })}
              </select>
            </div>
          )}
        </div>
      )}

      <div className="flex gap-2">
        <button onClick={() => onSubmit(form)}
          className="bg-blue-600 text-white px-3 py-1 rounded text-sm hover:bg-blue-700">Add</button>
        <button onClick={onCancel} className="text-gray-500 px-3 py-1 rounded text-sm hover:bg-gray-200">Cancel</button>
      </div>
    </div>
  )
}
