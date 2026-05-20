import { useEffect, useRef, useState } from 'react'

export function useQueueSocket() {
  const [events, setEvents] = useState([])
  const [status, setStatus] = useState('connecting')
  const wsRef = useRef(null)

  useEffect(() => {
    const ws = new WebSocket(`ws://${window.location.hostname}:8000/ws/queue`)
    wsRef.current = ws

    ws.onopen = () => setStatus('open')
    ws.onclose = () => setStatus('closed')
    ws.onerror = () => setStatus('closed')
    ws.onmessage = (e) => {
      try {
        const msg = JSON.parse(e.data)
        setEvents((prev) => {
          const next = [...prev, msg]
          return next.length > 200 ? next.slice(-200) : next
        })
      } catch { /* ignore */ }
    }

    return () => ws.close()
  }, [])

  return { events, status }
}
