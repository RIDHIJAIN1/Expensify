import type { ReactNode } from 'react'
import { Link } from 'react-router-dom'
import { BarChart3, ShieldCheck, Sparkles, Tags } from 'lucide-react'

const HIGHLIGHTS = [
  { icon: Tags, text: 'Seeded categories from Food to Investments, plus your own' },
  { icon: BarChart3, text: 'Interactive charts by category and time period' },
  { icon: ShieldCheck, text: 'Bank-grade security with httpOnly JWT sessions' },
]

export function AuthLayout({
  title,
  subtitle,
  children,
}: {
  title: string
  subtitle: ReactNode
  children: ReactNode
}) {
  return (
    <div className="flex min-h-screen bg-white">
      <div className="relative hidden w-[46%] overflow-hidden bg-ink-950 lg:flex lg:flex-col lg:justify-between">
        <div
          className="pointer-events-none absolute inset-0 opacity-50"
          style={{
            backgroundImage:
              'radial-gradient(circle at 20% 15%, #4f46e5 0%, transparent 42%), radial-gradient(circle at 90% 75%, #a21caf 0%, transparent 40%), radial-gradient(circle at 50% 50%, #1e1b4b 0%, transparent 60%)',
          }}
        />
        <div className="relative p-10">
          <Link to="/" className="flex items-center gap-2.5">
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-br from-indigo-500 to-violet-600 shadow-lg shadow-indigo-900/40">
              <span className="font-display text-sm font-extrabold text-white">E</span>
            </div>
            <span className="font-display text-lg font-bold text-white">Expensify</span>
          </Link>
        </div>

        <div className="relative px-10">
          <span className="inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-3 py-1.5 text-[11px] font-bold uppercase tracking-wider text-indigo-300">
            <Sparkles className="h-3.5 w-3.5" /> Expense intelligence
          </span>
          <h2 className="mt-5 font-display text-3xl font-extrabold leading-tight tracking-tight text-white">
            Every rupee,{' '}
            <span className="bg-gradient-to-r from-indigo-400 to-fuchsia-400 bg-clip-text text-transparent">
              accounted for.
            </span>
          </h2>
          <ul className="mt-8 space-y-4">
            {HIGHLIGHTS.map((item) => (
              <li key={item.text} className="flex items-start gap-3 text-sm text-slate-300">
                <span className="mt-0.5 flex h-7 w-7 shrink-0 items-center justify-center rounded-lg bg-white/10">
                  <item.icon className="h-3.5 w-3.5 text-indigo-300" />
                </span>
                {item.text}
              </li>
            ))}
          </ul>
        </div>

        <div className="relative p-10">
          <blockquote className="rounded-2xl border border-white/10 bg-white/5 p-5 backdrop-blur">
            <p className="text-sm leading-relaxed text-slate-300">
              “I uploaded three months of statements and instantly saw that food delivery was my
              second-biggest expense. That insight alone paid for itself.”
            </p>
            <footer className="mt-3 text-xs font-semibold text-indigo-300">
              — A very organized saver
            </footer>
          </blockquote>
        </div>
      </div>

      <div className="flex flex-1 items-center justify-center px-5 py-10 sm:px-10">
        <div className="w-full max-w-md animate-fade-up">
          <Link to="/" className="mb-8 flex items-center gap-2.5 lg:hidden">
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-br from-indigo-500 to-violet-600">
              <span className="font-display text-sm font-extrabold text-white">E</span>
            </div>
            <span className="font-display text-lg font-bold text-slate-900">Expensify</span>
          </Link>
          <h1 className="font-display text-2xl font-extrabold tracking-tight text-slate-900">
            {title}
          </h1>
          <p className="mt-2 text-sm text-slate-500">{subtitle}</p>
          <div className="mt-8">{children}</div>
        </div>
      </div>
    </div>
  )
}
