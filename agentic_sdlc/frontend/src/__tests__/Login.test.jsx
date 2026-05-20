import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import Login from '../pages/Login.jsx'

vi.mock('../api/auth.js', () => ({ login: vi.fn() }))
vi.mock('../store/authStore.js', () => ({ useAuthStore: () => ({ setToken: vi.fn() }) }))

describe('Login page', () => {
  it('renders email and password inputs', () => {
    render(<MemoryRouter><Login /></MemoryRouter>)
    expect(screen.getByPlaceholderText(/email/i)).toBeInTheDocument()
    expect(screen.getByPlaceholderText(/password/i)).toBeInTheDocument()
  })

  it('calls login API on submit', async () => {
    const { login } = await import('../api/auth.js')
    login.mockResolvedValue({ token: 'tok123' })
    render(<MemoryRouter><Login /></MemoryRouter>)
    fireEvent.change(screen.getByPlaceholderText(/email/i), { target: { value: 'u@example.com' } })
    fireEvent.change(screen.getByPlaceholderText(/password/i), { target: { value: 'pass' } })
    fireEvent.click(screen.getByRole('button', { name: /sign in/i }))
    await waitFor(() => expect(login).toHaveBeenCalledWith('u@example.com', 'pass'))
  })

  it('shows error on failed login', async () => {
    const { login } = await import('../api/auth.js')
    login.mockRejectedValue({ response: { data: { detail: 'Invalid credentials' } } })
    render(<MemoryRouter><Login /></MemoryRouter>)
    fireEvent.change(screen.getByPlaceholderText(/email/i), { target: { value: 'x@x.com' } })
    fireEvent.change(screen.getByPlaceholderText(/password/i), { target: { value: 'bad' } })
    fireEvent.click(screen.getByRole('button', { name: /sign in/i }))
    await waitFor(() => expect(screen.getByText(/invalid credentials/i)).toBeInTheDocument())
  })
})
