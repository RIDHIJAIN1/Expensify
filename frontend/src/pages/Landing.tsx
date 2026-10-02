import { Link } from 'react-router-dom'
import {
  ArrowRight,
  BarChart3,
  FileSpreadsheet,
  Sparkles,
  Tags,
  UploadCloud,
} from 'lucide-react'
import { useAuth } from '../auth/AuthContext'

const FEATURES = [
  {
    icon: UploadCloud,
    title: 'Drop a statement',
    body: 'Drag in a bank-statement CSV. The parser handles headers, dates, ₹ amounts and messy rows.',
  },
  {
    icon: Tags,
    title: 'Auto-categorized',
    body: 'Keyword rules sort every line — Food, Travel, Utilities, Shopping and more — and you can override.',
  },
  {
    icon: BarChart3,
    title: 'See the patterns',
    body: 'Donut, trend and merchant breakdowns across any date range, with day/week/month insight.',
  },
  {
    icon: FileSpreadsheet,
    title: 'Export anywhere',
    body: 'Download categorized data as CSV or a formatted PDF report in one click.',
  },
]

export default function Landing() {
  const { user } = useAuth()
  const appHref = user ? '/app/dashboard' : '/signup'

  return (
    <div className="min-h-screen bg-slate-50">
      <header className="sticky top-0 z-30 border-b border-slate-200/70 bg-white/80 backdrop-blur-lg">
        <div className="mx-auto flex h-16 max-w-6xl items-center justify-between px-5 lg:px-8">
          <div className="flex items-center gap-2.5">
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-br from-indigo-500 to-violet-600 shadow-lg shadow-indigo-500/25">
              <span className="font-display text-sm font-extrabold text-white">E</span>
            </div>
            <span className="font-display text-lg font-bold text-slate-900">Expensify</span>
          </div>
          <div className="flex items-center gap-2">
            {user ? (
              <Link
                to="/app/dashboard"
                className="inline-flex h-9 items-center gap-2 rounded-xl bg-gradient-to-r from-indigo-600 to-violet-600 px-4 text-sm font-semibold text-white shadow-sm shadow-indigo-600/25 transition hover:from-indigo-500 hover:to-violet-500"
              >
                Open app <ArrowRight className="h-3.5 w-3.5" />
              </Link>
            ) : (
              <>
                <Link
                  to="/login"
                  className="inline-flex h-9 items-center rounded-xl px-3.5 text-sm font-semibold text-slate-600 transition hover:bg-slate-100 hover:text-slate-900"
                >
                  Sign in
                </Link>
                <Link
                  to="/signup"
                  className="inline-flex h-9 items-center gap-2 rounded-xl bg-gradient-to-r from-indigo-600 to-violet-600 px-4 text-sm font-semibold text-white shadow-sm shadow-indigo-600/25 transition hover:from-indigo-500 hover:to-violet-500"
                >
                  Get started
                </Link>
              </>
            )}
          </div>
        </div>
      </header>

      <section className="relative overflow-hidden bg-ink-950">
        <div
          className="pointer-events-none absolute inset-0 opacity-60"
          style={{
            backgroundImage:
              'radial-gradient(circle at 15% 20%, #4f46e5 0%, transparent 40%), radial-gradient(circle at 85% 10%, #a21caf 0%, transparent 38%), radial-gradient(circle at 60% 100%, #0ea5e9 0%, transparent 42%)',
          }}
        />
        <div className="relative mx-auto max-w-6xl px-5 py-20 lg:px-8 lg:py-28">
          <div className="max-w-2xl animate-fade-up">
            <span className="inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-3 py-1.5 text-[11px] font-bold uppercase tracking-wider text-indigo-300">
              <Sparkles className="h-3.5 w-3.5" /> Expense intelligence
            </span>
            <h1 className="mt-6 font-display text-4xl font-extrabold leading-[1.1] tracking-tight text-white sm:text-5xl lg:text-6xl">
              Turn a bank statement into{' '}
              <span className="bg-gradient-to-r from-indigo-400 via-violet-400 to-fuchsia-400 bg-clip-text text-transparent">
                clear spending insights.
              </span>
            </h1>
            <p className="mt-6 max-w-xl text-base leading-relaxed text-slate-300">
              Upload a CSV and every transaction is parsed, de-duplicated and categorized
              automatically — then visualized across any time period, with CSV and PDF export.
            </p>
            <div className="mt-9 flex flex-wrap items-center gap-3">
              <Link
                to={appHref}
                className="inline-flex h-12 items-center gap-2 rounded-xl bg-gradient-to-r from-indigo-600 to-violet-600 px-6 text-sm font-bold text-white shadow-lg shadow-indigo-900/40 transition hover:from-indigo-500 hover:to-violet-500"
              >
                {user ? 'Open dashboard' : 'Start free'} <ArrowRight className="h-4 w-4" />
              </Link>
              <a
                href="/sample_statement.csv"
                download
                className="inline-flex h-12 items-center gap-2 rounded-xl border border-white/15 bg-white/5 px-6 text-sm font-semibold text-slate-200 backdrop-blur transition hover:bg-white/10"
              >
                Download sample CSV
              </a>
            </div>
          </div>
        </div>
      </section>

      <section className="mx-auto max-w-6xl px-5 py-16 lg:px-8 lg:py-20">
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {FEATURES.map((feature) => (
            <div key={feature.title} className="card p-6 transition-shadow hover:shadow-pop">
              <span className="flex h-11 w-11 items-center justify-center rounded-xl bg-indigo-50 text-indigo-600">
                <feature.icon className="h-5 w-5" strokeWidth={2.1} />
              </span>
              <h3 className="mt-4 font-display text-base font-bold text-slate-900">
                {feature.title}
              </h3>
              <p className="mt-2 text-sm leading-relaxed text-slate-500">{feature.body}</p>
            </div>
          ))}
        </div>
      </section>

      <footer className="border-t border-slate-200 bg-white">
        <div className="mx-auto flex max-w-6xl flex-col items-center justify-between gap-3 px-5 py-8 sm:flex-row lg:px-8">
          <div className="flex items-center gap-2">
            <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-gradient-to-br from-indigo-500 to-violet-600">
              <span className="font-display text-[11px] font-extrabold text-white">E</span>
            </div>
            <span className="font-display text-sm font-bold text-slate-900">Expensify</span>
          </div>
          <p className="text-xs text-slate-400">
            © {new Date().getFullYear()} Expensify. All rights reserved.
          </p>
        </div>
      </footer>
    </div>
  )
}
