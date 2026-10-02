import type { ReactNode } from 'react'
import { Navigate, useLocation } from 'react-router-dom'
import { useAuth } from '../auth/AuthContext'

export default function Protected({ children }: { children: ReactNode }) {
  const { user, loading } = useAuth()
  const location = useLocation()

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-[#f4f5fb]">
        <div className="flex items-center gap-2.5 text-slate-400">
          <span className="h-2 w-2 animate-pulse rounded-full bg-indigo-500" />
          <span className="text-sm font-medium">Loading…</span>
        </div>
      </div>
    )
  }

  if (!user) return <Navigate to="/login" replace state={{ from: location.pathname }} />

  return <>{children}</>
}
