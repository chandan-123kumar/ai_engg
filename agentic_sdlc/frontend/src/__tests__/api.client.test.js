import { describe, it, expect, beforeEach, vi } from 'vitest'

describe('API client', () => {
  beforeEach(() => { localStorage.clear(); vi.resetModules() })

  it('injects Authorization header when token exists', async () => {
    localStorage.setItem('token', 'test-token-123')
    const { default: client } = await import('../api/client.js')
    const config = client.interceptors.request.handlers[0].fulfilled({ headers: {} })
    expect(config.headers['Authorization']).toBe('Bearer test-token-123')
  })

  it('omits Authorization header when no token', async () => {
    const { default: client } = await import('../api/client.js')
    const config = client.interceptors.request.handlers[0].fulfilled({ headers: {} })
    expect(config.headers['Authorization']).toBeUndefined()
  })
})
