import client from './client.js'
export const login = (email, password) =>
  client.post('/auth/login', { email, password }).then((r) => r.data)
export const register = (name, email, password) =>
  client.post('/auth/register', { name, email, password }).then((r) => r.data)
