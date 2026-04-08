import axios from 'axios'
import client from './client'
import type { User } from '../types'

export const authApi = {
  // Логин через отдельный axios без shared client,
  // чтобы глобальный application/json не ломал form-urlencoded запрос
  login: (email: string, password: string) => {
    const params = new URLSearchParams()
    params.append('username', email)
    params.append('password', password)

    return axios.post<{ access_token: string; token_type: string }>(
      '/api/v1/auth/login',
      params,
      {
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
      }
    ).then(r => r.data)
  },

  register: (email: string, name: string, password: string) =>
    client.post<User>('/auth/register', { email, name, password }).then(r => r.data),

  me: () => client.get<User>('/auth/me').then(r => r.data)
}