import type { ReactNode } from 'react'
import type { LucideIcon } from 'lucide-react'
import { TrendingDown, TrendingUp } from 'lucide-react'
import { cn } from '../../lib/cn'
import { formatPercent } from '../../lib/format'

export function StatCard({
  label,
  value,
  icon: Icon,
  iconClass,
  delta,
  deltaLabel,
  invertDelta = false,
  spark,
}: {
  label: string
  value: ReactNode
  icon: LucideIcon
  iconClass: string
  delta?: number | null
  deltaLabel?: string
  invertDelta?: boolean
  spark?: ReactNode
}) {
  const hasDelta = delta !== null && delta !== undefined
  const isUp = hasDelta && delta! >= 0
  const isGood = invertDelta ? !isUp : isUp

  return (
    <div className="card group relative overflow-hidden p-5 transition-all hover:-translate-y-0.5 hover:shadow-pop">
      <div className="pointer-events-none absolute -right-8 -top-8 h-24 w-24 rounded-full bg-gradient-to-br from-indigo-500/5 to-violet-500/10 transition-transform duration-500 group-hover:scale-150" />
      <div className="relative flex items-start justify-between">
        <div>
          <p className="text-xs font-semibold uppercase tracking-wider text-slate-400">{label}</p>
          <p className="mt-2 font-display text-2xl font-bold tracking-tight tabular-nums text-slate-900">
            {value}
          </p>
        </div>
        <span className={cn('flex h-10 w-10 items-center justify-center rounded-xl', iconClass)}>
          <Icon className="h-5 w-5" strokeWidth={2.2} />
        </span>
      </div>

      {spark ? <div className="relative mt-3 opacity-90">{spark}</div> : null}

      {hasDelta ? (
        <div className="relative mt-3 flex items-center gap-1.5 text-xs">
          <span
            className={cn(
              'inline-flex items-center gap-1 rounded-full px-2 py-0.5 font-bold',
              isGood ? 'bg-emerald-50 text-emerald-700' : 'bg-rose-50 text-rose-700',
            )}
          >
            {isUp ? <TrendingUp className="h-3 w-3" /> : <TrendingDown className="h-3 w-3" />}
            {formatPercent(delta!)}
          </span>
          <span className="text-slate-400">{deltaLabel ?? 'vs previous period'}</span>
        </div>
      ) : deltaLabel ? (
        <p className="relative mt-3 text-xs text-slate-400">{deltaLabel}</p>
      ) : null}
    </div>
  )
}
