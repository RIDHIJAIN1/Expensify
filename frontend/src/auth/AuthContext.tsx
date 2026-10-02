import { useQueryClient } from '@tanstack/react-query'
import { createContext, useContext, useEffect, useState, type ReactNode } from 'react'
import { api } from '../lib/api'
import type { User } from '../lib/types'

interface AuthContextValue {
  user: User | null
  loading: boolean
  login: (email: string, password: string) => Promise<void>
  signup: (email: string, password: string, name: string) => Promise<void>
  logout: () => Promise<void>
}

const AuthContext = createContext<AuthContextValue | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)
  const queryClient = useQueryClient()

  useEffect(() => {
    api<User>('/api/auth/me')
      .then(setUser)
      .catch(() => setUser(null))
      .finally(() => setLoading(false))
  }, [])

  // When a request can't be recovered (refresh failed), clear the session.
  useEffect(() => {
    const onUnauthorized = () => {
      sessionStorage.setItem('sessionExpired', '1')
      queryClient.clear()
      setUser(null)
    }
    window.addEventListener('auth:unauthorized', onUnauthorized)
    return () => window.removeEventListener('auth:unauthorized', onUnauthorized)
  }, [queryClient])

  async function login(email: string, password: string) {
    const u = await api<User>('/api/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password }),
    })
    queryClient.clear()
    setUser(u)
  }

  async function signup(email: string, password: string, name: string) {
    const u = await api<User>('/api/auth/signup', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password, name }),
    })
    queryClient.clear()
    setUser(u)
  }

  async function logout() {
    try {
      await api('/api/auth/logout', { method: 'POST' })
    } finally {
      queryClient.clear()
      setUser(null)
    }
  }

  return (
    <AuthContext.Provider value={{ user, loading, login, signup, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within AuthProvider')
  return ctx
}
