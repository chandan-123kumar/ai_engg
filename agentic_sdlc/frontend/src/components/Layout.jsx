import { NavLink, useNavigate } from 'react-router-dom'
import { useAuthStore } from '../store/authStore.js'

export default function Layout({ children }) {
  const logout = useAuthStore((s) => s.logout)
  const navigate = useNavigate()

  return (
    <div className="min-h-screen flex flex-col bg-gray-100">
      <header className="bg-gray-900 text-white flex items-center px-6 h-12 gap-6">
        <span className="font-bold text-sm tracking-wide">Agentic WF</span>
        <NavLink to="/queue"
          className={({ isActive }) => `text-sm px-3 py-1 rounded ${isActive ? 'bg-blue-600' : 'hover:bg-gray-700'}`}>
          Queue
        </NavLink>
        <NavLink to="/admin"
          className={({ isActive }) => `text-sm px-3 py-1 rounded ${isActive ? 'bg-blue-600' : 'hover:bg-gray-700'}`}>
          Admin
        </NavLink>
        <button onClick={() => { logout(); navigate('/login') }}
          className="ml-auto text-sm px-3 py-1 bg-red-600 hover:bg-red-700 rounded">
          Logout
        </button>
      </header>
      <main className="flex-1 p-6">{children}</main>
    </div>
  )
}
