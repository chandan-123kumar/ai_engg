import { useMemo } from 'react'
import Layout from '../components/Layout.jsx'
import { useQueueSocket } from '../hooks/useQueueSocket.js'

const DOT = { open: 'bg-green-400', connecting: 'bg-yellow-400 animate-pulse', closed: 'bg-red-400' }

function deriveActive(events, executorType) {
  const byExec = new Map()
  for (const ev of events) {
    if (ev.executor_type === executorType) byExec.set(ev.stage_execution_id, ev)
  }
  return [...byExec.values()].filter(
    (ev) => !['completed', 'failed', 'halted'].includes(ev.run_status)
  )
}

function AgentCard({ task }) {
  return (
    <div className="bg-white border-l-4 border-yellow-400 rounded-lg p-4 shadow-sm">
      <div className="flex justify-between items-center">
        <span className="font-semibold text-gray-800 text-sm">Agent task</span>
        <span className="bg-yellow-100 text-yellow-700 text-xs px-2 py-0.5 rounded animate-pulse">running</span>
      </div>
      <p className="text-xs text-gray-400 mt-1">
        run <code className="bg-gray-100 px-1 rounded">{task.run_id?.slice(0, 8)}…</code>
        {' · '}
        exec <code className="bg-gray-100 px-1 rounded">{task.stage_execution_id?.slice(0, 8)}…</code>
      </p>
    </div>
  )
}

function HumanCard({ task }) {
  return (
    <div className="bg-white border-l-4 border-red-400 rounded-lg p-4 shadow-sm">
      <div className="flex justify-between items-center">
        <span className="font-semibold text-gray-800 text-sm">Human approval</span>
        <span className="bg-red-100 text-red-700 text-xs px-2 py-0.5 rounded">waiting</span>
      </div>
      <p className="text-xs text-gray-400 mt-1">
        run <code className="bg-gray-100 px-1 rounded">{task.run_id?.slice(0, 8)}…</code>
        {' · '}
        exec <code className="bg-gray-100 px-1 rounded">{task.stage_execution_id?.slice(0, 8)}…</code>
      </p>
      <div className="flex gap-2 mt-3">
        <button className="bg-green-600 text-white px-3 py-1 rounded text-xs hover:bg-green-700">Approve</button>
        <button className="bg-red-600 text-white px-3 py-1 rounded text-xs hover:bg-red-700">Reject</button>
      </div>
    </div>
  )
}

function EmptyState({ icon, label }) {
  return (
    <div className="flex flex-col items-center justify-center h-40 text-gray-300">
      <span className="text-4xl">{icon}</span>
      <span className="text-sm mt-2">{label}</span>
    </div>
  )
}

export default function Queue() {
  const { events, status } = useQueueSocket()

  const agentTasks = useMemo(() => deriveActive(events, 'agent'), [events])
  const humanTasks = useMemo(() => deriveActive(events, 'human'), [events])

  return (
    <Layout>
      <div className="flex items-center justify-between mb-4">
        <h1 className="text-xl font-bold text-gray-800">Live Queue</h1>
        <div className="flex items-center gap-2">
          <span className={`w-2 h-2 rounded-full ${DOT[status]}`} />
          <span className="text-xs text-gray-400 capitalize">{status}</span>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-6">
        <div>
          <h2 className="text-sm font-semibold text-gray-600 uppercase tracking-wide mb-3">
            Agent Queue{' '}
            <span className="ml-1 bg-yellow-100 text-yellow-700 px-1.5 py-0.5 rounded text-xs">{agentTasks.length}</span>
          </h2>
          <div className="space-y-3">
            {agentTasks.length === 0
              ? <EmptyState icon="🤖" label="No active agent tasks" />
              : agentTasks.map((t) => <AgentCard key={t.stage_execution_id} task={t} />)}
          </div>
        </div>

        <div>
          <h2 className="text-sm font-semibold text-gray-600 uppercase tracking-wide mb-3">
            Human Queue{' '}
            <span className="ml-1 bg-red-100 text-red-700 px-1.5 py-0.5 rounded text-xs">{humanTasks.length}</span>
          </h2>
          <div className="space-y-3">
            {humanTasks.length === 0
              ? <EmptyState icon="👤" label="No pending approvals" />
              : humanTasks.map((t) => <HumanCard key={t.stage_execution_id} task={t} />)}
          </div>
        </div>
      </div>
    </Layout>
  )
}
