import { useState, type FormEvent } from 'react'
import { Link, Navigate, useNavigate } from 'react-router-dom'
import { Lock, Mail, User as UserIcon } from 'lucide-react'
import { AuthLayout } from '../auth/AuthLayout'
import { useAuth } from '../auth/AuthContext'
import { Button } from '../components/ui/Button'
import { Input } from '../components/ui/Input'

export default function Signup() {
  const { user, signup } = useAuth()
  const navigate = useNavigate()
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')

  if (user) return <Navigate to="/app/dashboard" replace />

  const onSubmit = async (e: FormEvent) => {
    e.preventDefault()
    setError('')
    try {
      await signup(email, password, name)
      navigate('/app/dashboard', { replace: true })
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Signup failed')
    }
  }

  return (
    <AuthLayout
      title="Create your account"
      subtitle={
        <>
          Already have one?{' '}
          <Link to="/login" className="font-semibold text-indigo-600 transition hover:text-indigo-500">
            Sign in
          </Link>
        </>
      }
    >
      <form onSubmit={onSubmit} className="space-y-5">
        {error ? (
          <div className="rounded-xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm font-medium text-rose-700 animate-fade-in">
            {error}
          </div>
        ) : null}

        <Input
          label="Name"
          type="text"
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="Ridhi"
          autoComplete="name"
          icon={<UserIcon className="h-4 w-4" />}
        />
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
          minLength={8}
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          placeholder="At least 8 characters"
          autoComplete="new-password"
          hint="Minimum 8 characters."
          icon={<Lock className="h-4 w-4" />}
        />

        <Button type="submit" size="lg" className="w-full">
          Create account
        </Button>
      </form>
    </AuthLayout>
  )
}
