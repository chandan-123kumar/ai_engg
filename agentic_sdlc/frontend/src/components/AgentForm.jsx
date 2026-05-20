import { useState } from 'react'

export default function AgentForm({ onSubmit, onCancel }) {
  const [form, setForm] = useState({ agent_type: '', name: '', provider: 'claude_cli', provider_config: '{}', input_schema: '{}', output_schema: '{}' })
  const [err, setErr] = useState('')
  const set = (k, v) => setForm((f) => ({ ...f, [k]: v }))

  const handleSubmit = () => {
    try {
      onSubmit({ ...form, provider_config: JSON.parse(form.provider_config), input_schema: JSON.parse(form.input_schema), output_schema: JSON.parse(form.output_schema) })
      setErr('')
    } catch { setErr('provider_config, input_schema, output_schema must be valid JSON') }
  }

  return (
    <div className="bg-gray-50 border rounded p-3 space-y-2">
      <p className="text-xs font-semibold text-gray-600">Register Agent</p>
      <div className="flex gap-2">
        <input placeholder="Agent type (e.g. coder)" value={form.agent_type} onChange={(e) => set('agent_type', e.target.value)}
          className="flex-1 border rounded px-2 py-1.5 text-sm" />
        <input placeholder="Display name" value={form.name} onChange={(e) => set('name', e.target.value)}
          className="flex-1 border rounded px-2 py-1.5 text-sm" />
      </div>
      <select value={form.provider} onChange={(e) => set('provider', e.target.value)}
        className="w-full border rounded px-2 py-1.5 text-sm">
        <option value="claude_cli">Claude CLI</option>
        <option value="claude_api">Claude API</option>
      </select>
      <textarea value={form.provider_config} onChange={(e) => set('provider_config', e.target.value)}
        rows={3} placeholder='{"model": "claude-sonnet-4-6"}'
        className="w-full border rounded px-2 py-1.5 text-sm font-mono" />
      {err && <p className="text-red-600 text-xs">{err}</p>}
      <div className="flex gap-2">
        <button onClick={handleSubmit}
          className="bg-purple-600 text-white px-3 py-1 rounded text-sm hover:bg-purple-700">Register</button>
        <button onClick={onCancel} className="text-gray-500 px-3 py-1 rounded text-sm hover:bg-gray-200">Cancel</button>
      </div>
    </div>
  )
}
