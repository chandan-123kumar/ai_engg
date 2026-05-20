import { useState } from 'react'

export default function SubStepForm({ onSubmit, onCancel }) {
  const [form, setForm] = useState({
    name: '', order: 1, executor_type: 'agent',
    agent_conversation_config: { participants: ['coder'], initiator: 'coder', termination: { condition: 'single_turn', max_turns: 1 } },
    on_complete: 'next_step', on_reject: 'halt',
  })
  const set = (k, v) => setForm((f) => ({ ...f, [k]: v }))
  const setCondition = (condition) => set('agent_conversation_config', {
    ...form.agent_conversation_config,
    termination: { ...form.agent_conversation_config.termination, condition },
  })

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
        <select value={form.agent_conversation_config.termination.condition}
          onChange={(e) => setCondition(e.target.value)}
          className="flex-1 border rounded px-2 py-1.5 text-sm">
          <option value="single_turn">Single turn</option>
          <option value="reviewer_approves">Reviewer approves</option>
          <option value="max_turns">Max turns</option>
          <option value="tool_success">Tool success</option>
        </select>
      </div>
      <div className="flex gap-2">
        <button onClick={() => onSubmit(form)}
          className="bg-blue-600 text-white px-3 py-1 rounded text-sm hover:bg-blue-700">Add</button>
        <button onClick={onCancel} className="text-gray-500 px-3 py-1 rounded text-sm hover:bg-gray-200">Cancel</button>
      </div>
    </div>
  )
}
