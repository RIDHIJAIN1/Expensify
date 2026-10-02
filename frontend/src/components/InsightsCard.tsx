import type { LucideIcon } from 'lucide-react'
import {
  Activity,
  ArrowDownRight,
  ArrowUpRight,
  Minus,
  PiggyBank,
  Receipt,
  Sparkles,
  Store,
  Tag,
  TrendingUp,
} from 'lucide-react'
import { cn } from '../lib/cn'
import type { Insight } from '../lib/types'

const ICONS: Record<string, LucideIcon> = {
  'trend-up': ArrowUpRight,
  'trend-down': ArrowDownRight,
  'trend-flat': Minus,
  piggy: PiggyBank,
  category: Tag,
  growth: TrendingUp,
  store: Store,
  receipt: Receipt,
}

const TONES: Record<string, string> = {
  positive: 'bg-emerald-50 text-emerald-600',
  warning: 'bg-rose-50 text-rose-600',
  neutral: 'bg-slate-100 text-slate-600',
  info: 'bg-indigo-50 text-indigo-600',
}

export function InsightsCard({
  insights,
  loading,
}: {
  insights: Insight[]
  loading: boolean
}) {
  return (
    <div className="card h-full p-5 sm:p-6">
      <div className="mb-4 flex items-center justify-between">
        <div>
          <h2 className="font-display text-base font-bold text-slate-900">Insights</h2>
          <p className="text-xs text-slate-500">What changed in this period</p>
        </div>
        <Sparkles className="h-5 w-5 text-slate-300" />
      </div>

      {loading ? (
        <div className="space-y-3">
          {Array.from({ length: 4 }).map((_, index) => (
            <div key={index} className="skeleton h-12" />
          ))}
        </div>
      ) : insights.length === 0 ? (
        <p className="py-12 text-center text-sm text-slate-400">
          Not enough data yet. Upload a statement to see insights.
        </p>
      ) : (
        <ul className="space-y-3.5">
          {insights.map((item, index) => {
            const Icon = ICONS[item.icon] ?? Activity
            return (
              <li key={index} className="flex items-start gap-3">
                <span
                  className={cn(
                    'flex h-9 w-9 shrink-0 items-center justify-center rounded-xl',
                    TONES[item.tone] ?? TONES.neutral,
                  )}
                >
                  <Icon className="h-4 w-4" strokeWidth={2.2} />
                </span>
                <div className="min-w-0">
                  <p className="text-sm font-semibold text-slate-800">{item.title}</p>
                  <p className="mt-0.5 text-xs leading-relaxed text-slate-500">{item.detail}</p>
                </div>
              </li>
            )
          })}
        </ul>
      )}
    </div>
  )
}
