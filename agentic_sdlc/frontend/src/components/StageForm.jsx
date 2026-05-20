import { useState } from 'react'

export default function StageForm({ onSubmit, onCancel, agents = [] }) {
  const [form, setForm] = useState({
    name: '', order: 1, executor_type: 'agent', gate_type: 'none', config: {},
  })
  const set = (k, v) => setForm((f) => ({ ...f, [k]: v }))

  const agentType = form.config.agent_type || ''
  const setAgent = (v) => set('config', v ? { agent_type: v } : {})

  return (
    <div className="bg-gray-50 border rounded p-3 space-y-2">
      <p className="text-xs font-semibold text-gray-600">New Stage</p>
      <input placeholder="Stage name" value={form.name} onChange={(e) => set('name', e.target.value)}
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
        <select value={form.gate_type} onChange={(e) => set('gate_type', e.target.value)}
          className="flex-1 border rounded px-2 py-1.5 text-sm">
          <option value="none">No gate</option>
          <option value="github_pr">GitHub PR</option>
          <option value="slack">Slack</option>
          <option value="email">Email</option>
        </select>
      </div>
      {form.executor_type === 'agent' && (
        <select value={agentType} onChange={(e) => setAgent(e.target.value)}
          className="w-full border rounded px-2 py-1.5 text-sm">
          <option value="">— Assign agent (optional) —</option>
          {agents.map((a) => (
            <option key={a.agent_type} value={a.agent_type}>{a.name} ({a.agent_type})</option>
          ))}
        </select>
      )}
      <div className="flex gap-2">
        <button onClick={() => onSubmit(form)}
          className="bg-blue-600 text-white px-3 py-1 rounded text-sm hover:bg-blue-700">Add</button>
        <button onClick={onCancel} className="text-gray-500 px-3 py-1 rounded text-sm hover:bg-gray-200">Cancel</button>
      </div>
    </div>
  )
}
