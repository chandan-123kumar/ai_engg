import { describe, it, expect, beforeEach, vi } from 'vitest'

describe('authStore', () => {
  beforeEach(() => { localStorage.clear(); vi.resetModules() })

  it('setToken stores token in localStorage and state', async () => {
    const { useAuthStore } = await import('../store/authStore.js')
    useAuthStore.getState().setToken('abc123')
    expect(localStorage.getItem('token')).toBe('abc123')
    expect(useAuthStore.getState().token).toBe('abc123')
  })

  it('logout clears token from store and localStorage', async () => {
    const { useAuthStore } = await import('../store/authStore.js')
    useAuthStore.getState().setToken('abc123')
    useAuthStore.getState().logout()
    expect(localStorage.getItem('token')).toBeNull()
    expect(useAuthStore.getState().token).toBeNull()
  })
})
