import { useEffect, useState, type FormEvent } from 'react'
import { Link, Navigate, useLocation, useNavigate } from 'react-router-dom'
import { Info, Lock, Mail } from 'lucide-react'
import { AuthLayout } from '../auth/AuthLayout'
import { useAuth } from '../auth/AuthContext'
import { Button } from '../components/ui/Button'
import { Input } from '../components/ui/Input'

export default function Login() {
  const { user, login } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')

  useEffect(() => {
    if (sessionStorage.getItem('sessionExpired')) {
      setNotice('Your session expired. Please sign in again.')
      sessionStorage.removeItem('sessionExpired')
    }
  }, [])

  if (user) return <Navigate to="/app/dashboard" replace />

  const onSubmit = async (e: FormEvent) => {
    e.preventDefault()
    setError('')
    try {
      await login(email, password)
      const from = (location.state as { from?: string } | null)?.from
      navigate(from ?? '/app/dashboard', { replace: true })
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Login failed')
    }
  }

  return (
    <AuthLayout
      title="Welcome back"
      subtitle={
        <>
          New here?{' '}
          <Link to="/signup" className="font-semibold text-indigo-600 transition hover:text-indigo-500">
            Create an account
          </Link>
        </>
      }
    >
      <form onSubmit={onSubmit} className="space-y-5">
        {notice && (
          <div className="flex items-start gap-2 rounded-xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm font-medium text-slate-600 animate-fade-in">
            <Info className="mt-0.5 h-4 w-4 shrink-0 text-slate-400" />
            {notice}
          </div>
        )}
        {error ? (
          <div className="rounded-xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm font-medium text-rose-700 animate-fade-in">
            {error}
          </div>
        ) : null}

        <Input
          label="Email address"
          type="email"
          required
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          placeholder="you@example.com"
          autoComplete="email"
          icon={<Mail className="h-4 w-4" />}
        />
        <Input
          label="Password"
          type="password"
          required
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          placeholder="••••••••"
          autoComplete="current-password"
          icon={<Lock className="h-4 w-4" />}
        />

        <Button type="submit" size="lg" className="w-full">
          Sign in
        </Button>

        <p className="text-center text-xs text-slate-400">
          Sessions are secured with httpOnly cookies and rotate automatically.
        </p>
      </form>
    </AuthLayout>
  )
}
