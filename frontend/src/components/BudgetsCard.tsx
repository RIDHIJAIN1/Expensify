import { Settings2, Target } from 'lucide-react'
import { Button } from './ui/Button'
import { cn } from '../lib/cn'
import { formatCompactCurrency, formatCurrency } from '../lib/format'
import type { Budget } from '../lib/types'

export function BudgetsCard({
  budgets,
  loading,
  onManage,
}: {
  budgets: Budget[]
  loading: boolean
  onManage: () => void
}) {
  const totalLimit = budgets.reduce((sum, b) => sum + Number(b.limit), 0)
  const totalSpent = budgets.reduce((sum, b) => sum + Number(b.spent), 0)
  const overCount = budgets.filter((b) => b.over).length

  return (
    <div className="card h-full p-5 sm:p-6">
      <div className="mb-4 flex items-center justify-between gap-3">
        <div>
          <h2 className="font-display text-base font-bold text-slate-900">Budgets</h2>
          <p className="text-xs text-slate-500">
            {budgets.length > 0
              ? `${formatCurrency(totalSpent)} of ${formatCurrency(totalLimit)} used`
              : 'Set limits per category'}
          </p>
        </div>
        <Button
          variant="secondary"
          size="sm"
          icon={<Settings2 className="h-3.5 w-3.5" />}
          onClick={onManage}
        >
          Manage
        </Button>
      </div>

      {loading ? (
        <div className="space-y-4">
          {Array.from({ length: 3 }).map((_, index) => (
            <div key={index} className="skeleton h-12" />
          ))}
        </div>
      ) : budgets.length === 0 ? (
        <div className="flex flex-col items-center py-10 text-center">
          <span className="mb-3 flex h-12 w-12 items-center justify-center rounded-2xl bg-indigo-50 text-indigo-600">
            <Target className="h-5 w-5" />
          </span>
          <p className="text-sm font-semibold text-slate-700">No budgets yet</p>
          <p className="mt-1 max-w-xs text-xs text-slate-500">
            Set a spending limit per category and track progress against it.
          </p>
          <Button className="mt-4" size="sm" onClick={onManage}>
            Set budgets
          </Button>
        </div>
      ) : (
        <div className="space-y-4">
          {overCount > 0 && (
            <p className="rounded-lg bg-rose-50 px-3 py-2 text-xs font-semibold text-rose-700">
              {overCount} categor{overCount === 1 ? 'y' : 'ies'} over budget
            </p>
          )}
          {budgets.slice(0, 6).map((b) => (
            <div key={b.category_id}>
              <div className="mb-1.5 flex items-center justify-between gap-3 text-sm">
                <span className="flex min-w-0 items-center gap-2 font-semibold text-slate-700">
                  <span
                    className="h-2.5 w-2.5 shrink-0 rounded-full"
                    style={{ backgroundColor: b.color || '#94a3b8' }}
                  />
                  <span className="truncate">{b.category_name}</span>
                </span>
                <span className="shrink-0 tabular-nums font-bold text-slate-900">
                  {formatCompactCurrency(b.spent)}
                  <span className="font-medium text-slate-400"> / {formatCompactCurrency(b.limit)}</span>
                </span>
              </div>
              <div className="h-2 w-full overflow-hidden rounded-full bg-slate-100">
                <div
                  className={cn(
                    'h-full rounded-full transition-all duration-700',
                    b.over
                      ? 'bg-gradient-to-r from-rose-500 to-red-500'
                      : 'bg-gradient-to-r from-indigo-500 to-violet-500',
                  )}
                  style={{ width: `${Math.min(Math.max(b.percent, 2), 100)}%` }}
                />
              </div>
              <p
                className={cn(
                  'mt-1 text-[11px]',
                  b.over ? 'font-semibold text-rose-600' : 'text-slate-400',
                )}
              >
                {b.over
                  ? `Over by ${formatCurrency(Math.abs(Number(b.remaining)))}`
                  : `${formatCurrency(b.remaining)} left`}{' '}
                · {b.percent.toFixed(0)}%
              </p>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
