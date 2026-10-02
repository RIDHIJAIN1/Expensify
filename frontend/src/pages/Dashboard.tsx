import { useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import confetti from 'canvas-confetti'
import {
  AlertTriangle,
  ArrowDownRight,
  ArrowUpRight,
  BarChart3,
  CalendarDays,
  CheckCircle2,
  FileSpreadsheet,
  FileText,
  PiggyBank,
  ReceiptText,
  RefreshCw,
  Sparkles,
  Store,
  UploadCloud,
  XCircle,
} from 'lucide-react'
import { DateRangePicker, presetRange } from '../components/DateRangePicker'
import { SpendTrendChart } from '../components/charts/SpendTrendChart'
import { CategoryDonut, type DonutDatum } from '../components/charts/CategoryDonut'
import { StatCard } from '../components/dashboard/StatCard'
import { CategoryIcon } from '../components/CategoryIcon'
import { MerchantAvatar } from '../components/MerchantAvatar'
import { SavingsRing } from '../components/SavingsRing'
import { Sparkline } from '../components/Sparkline'
import { AnimatedValue } from '../components/AnimatedValue'
import { ImportBar } from '../components/ImportBar'
import { BudgetsCard } from '../components/BudgetsCard'
import { BudgetModal } from '../components/BudgetModal'
import { InsightsCard } from '../components/InsightsCard'
import { Button } from '../components/ui/Button'
import { Badge } from '../components/ui/Badge'
import { EmptyState } from '../components/ui/EmptyState'
import { useToast } from '../context/ToastContext'
import { useFileDrop } from '../hooks/useFileDrop'
import { api, download, uploadFile } from '../lib/api'
import { cn } from '../lib/cn'
import {
  formatCompactCurrency,
  formatCurrency,
  formatDate,
  formatDateTimeSafe,
} from '../lib/format'
import type { Budget, Category, DateRange, Insight, Summary, TransactionList, Upload } from '../lib/types'

const PALETTE = [
  '#4f46e5', '#0ea5e9', '#14b8a6', '#f59e0b',
  '#f43f5e', '#8b5cf6', '#64748b', '#22c55e',
]

function defaultRange(): DateRange {
  return presetRange(3, 0)
}

function paramsOf(range: DateRange, extra: Record<string, string> = {}) {
  return new URLSearchParams({ date_from: range.from, date_to: range.to, ...extra }).toString()
}

export default function Dashboard() {
  const [range, setRange] = useState<DateRange>(defaultRange)
  const [budgetOpen, setBudgetOpen] = useState(false)
  const queryClient = useQueryClient()
  const toast = useToast()

  const summary = useQuery({
    queryKey: ['summary', range.from, range.to],
    queryFn: () => api<Summary>(`/api/summary?${paramsOf(range)}`),
  })

  const categories = useQuery({
    queryKey: ['categories'],
    queryFn: () => api<Category[]>('/api/categories'),
  })

  const recent = useQuery({
    queryKey: ['transactions', 'recent', range.from, range.to],
    queryFn: () => api<TransactionList>(`/api/transactions?${paramsOf(range, { limit: '6' })}`),
  })

  const uploads = useQuery({
    queryKey: ['uploads'],
    queryFn: () => api<Upload[]>('/api/uploads'),
  })

  const budgets = useQuery({
    queryKey: ['budgets', range.from, range.to],
    queryFn: () => api<Budget[]>(`/api/budgets?${paramsOf(range)}`),
  })

  const insights = useQuery({
    queryKey: ['insights', range.from, range.to],
    queryFn: () => api<Insight[]>(`/api/insights?${paramsOf(range)}`),
  })

  const upload = useMutation({
    mutationFn: (file: File) => uploadFile(file),
    onSuccess: (result: Upload) => {
      queryClient.invalidateQueries({ queryKey: ['summary'] })
      queryClient.invalidateQueries({ queryKey: ['transactions'] })
      queryClient.invalidateQueries({ queryKey: ['uploads'] })
      queryClient.invalidateQueries({ queryKey: ['categories'] })
      if (result.status === 'FAILED') {
        toast.error('Upload failed', result.error_summary?.[0])
        return
      }
      confetti({
        particleCount: 90,
        spread: 75,
        origin: { y: 0.28 },
        colors: ['#6366f1', '#a855f7', '#10b981', '#f59e0b'],
        disableForReducedMotion: true,
      })
      toast.success(
        `Imported ${result.filename}`,
        `${result.imported_count} imported · ${result.duplicate_count} duplicates`,
      )
    },
    onError: (error) => toast.error('Upload failed', (error as Error).message),
  })

  const dragging = useFileDrop(upload.mutate)

  const colorById = useMemo(() => {
    const map = new Map<number, string>()
    ;(categories.data || []).forEach((c) => {
      if (c.color) map.set(c.id, c.color)
    })
    return map
  }, [categories.data])

  const donutData: DonutDatum[] = useMemo(
    () =>
      (summary.data?.by_category || [])
        .map((c, i) => ({
          name: c.category_name,
          total: Number(c.total),
          count: c.count,
          color: (c.category_id && colorById.get(c.category_id)) || PALETTE[i % PALETTE.length],
        }))
        .sort((a, b) => b.total - a.total),
    [summary.data, colorById],
  )

  const months = summary.data?.by_month ?? []
  const spentSeries = months.map((m) => Number(m.debit))
  const incomeSeries = months.map((m) => Number(m.credit))
  const netSeries = months.map((m) => Number(m.credit) - Number(m.debit))
  const countSeries = months.map((m) => m.count)

  const hasData = (summary.data?.transaction_count ?? 0) > 0
  const spent = Number(summary.data?.total_spent ?? 0)
  const income = Number(summary.data?.total_income ?? 0)
  const net = Number(summary.data?.net ?? 0)
  const savingsRate = income > 0 ? Math.round((net / income) * 100) : 0
  const days = Math.max(
    1,
    Math.round((new Date(range.to).getTime() - new Date(range.from).getTime()) / 86_400_000),
  )
  const maxMerchant = Math.max(...(summary.data?.top_merchants.map((m) => Number(m.total)) ?? [1]), 1)

  const refreshAll = () => {
    summary.refetch()
    recent.refetch()
    uploads.refetch()
    budgets.refetch()
    insights.refetch()
  }

  const handleExport = async (kind: 'csv' | 'pdf') => {
    try {
      await download(`/api/export/${kind}?${paramsOf(range)}`, `expense-report.${kind}`)
      toast.success(`${kind.toUpperCase()} report downloaded`)
    } catch {
      toast.error('Export failed', 'Please try again in a moment.')
    }
  }

  return (
    <div className="space-y-6 animate-fade-up">
      {dragging ? (
        <div className="fixed inset-0 z-[90] flex items-center justify-center bg-ink-950/50 p-6 backdrop-blur-sm animate-fade-in">
          <div className="flex flex-col items-center gap-3 rounded-3xl border-2 border-dashed border-indigo-300 bg-white/95 px-16 py-14 text-center shadow-pop">
            <span className="flex h-16 w-16 items-center justify-center rounded-2xl bg-gradient-to-br from-indigo-600 to-violet-600 text-white">
              <UploadCloud className="h-7 w-7" />
            </span>
            <p className="font-display text-lg font-bold text-slate-900">Drop to import</p>
            <p className="text-sm text-slate-500">Release your CSV to categorize it instantly</p>
          </div>
        </div>
      ) : null}

      <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
        <div>
          <h1 className="font-display text-2xl font-extrabold tracking-tight text-slate-900">
            Dashboard
          </h1>
          <p className="mt-1 text-sm text-slate-500">
            Your spending overview for {formatDate(range.from)} – {formatDate(range.to)}
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <DateRangePicker value={range} onChange={setRange} />
          <Button variant="secondary" icon={<RefreshCw className="h-3.5 w-3.5" />} onClick={refreshAll}>
            Refresh
          </Button>
          <Button
            variant="secondary"
            icon={<FileSpreadsheet className="h-3.5 w-3.5" />}
            onClick={() => handleExport('csv')}
          >
            CSV
          </Button>
          <Button variant="dark" icon={<FileText className="h-3.5 w-3.5" />} onClick={() => handleExport('pdf')}>
            PDF
          </Button>
        </div>
      </div>

      <ImportBar onFile={upload.mutate} pending={upload.isPending} active={dragging} />

      {summary.isError ? (
        <div className="card flex items-center justify-between p-5">
          <p className="text-sm font-medium text-rose-600">{(summary.error as Error).message}</p>
          <Button variant="secondary" size="sm" onClick={refreshAll}>
            Retry
          </Button>
        </div>
      ) : null}

      {!summary.isLoading && summary.data && !hasData ? (
        <div className="card">
          <EmptyState
            icon={Sparkles}
            title="No transactions in this period"
            description="Drop a bank statement CSV above (or anywhere on this page) and it will be categorized automatically."
          />
        </div>
      ) : (
        <>
          <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
            {summary.isLoading || !summary.data ? (
              Array.from({ length: 4 }).map((_, index) => (
                <div key={index} className="skeleton h-[168px]" />
              ))
            ) : (
              <>
                <StatCard
                  label="Total spent"
                  value={<AnimatedValue value={spent} />}
                  icon={ArrowUpRight}
                  iconClass="bg-indigo-50 text-indigo-600"
                  deltaLabel={`${summary.data.transaction_count} transactions`}
                  spark={<Sparkline data={spentSeries} color="#6366f1" />}
                />
                <StatCard
                  label="Income received"
                  value={<AnimatedValue value={income} />}
                  icon={ArrowDownRight}
                  iconClass="bg-emerald-50 text-emerald-600"
                  deltaLabel={`${savingsRate}% savings rate`}
                  spark={<Sparkline data={incomeSeries} color="#10b981" />}
                />
                <StatCard
                  label="Net savings"
                  value={<AnimatedValue value={net} />}
                  icon={PiggyBank}
                  iconClass="bg-violet-50 text-violet-600"
                  deltaLabel={`${savingsRate}% of income saved`}
                  spark={<Sparkline data={netSeries} color="#8b5cf6" />}
                />
                <StatCard
                  label="Transactions"
                  value={<AnimatedValue value={summary.data.transaction_count} format={(n) => Math.round(n).toLocaleString('en-IN')} />}
                  icon={CalendarDays}
                  iconClass="bg-sky-50 text-sky-600"
                  deltaLabel={`over ${days} days`}
                  spark={<Sparkline data={countSeries} color="#0ea5e9" />}
                />
              </>
            )}
          </div>

          <div className="grid gap-6 xl:grid-cols-5">
            <div className="card p-5 sm:p-6 xl:col-span-3">
              <div className="mb-5">
                <h2 className="font-display text-base font-bold text-slate-900">Spending trend</h2>
                <p className="text-xs text-slate-500">Money out vs money in, month by month</p>
              </div>
              {summary.isLoading || !summary.data ? (
                <div className="skeleton h-[300px] w-full" />
              ) : (
                <SpendTrendChart data={months} />
              )}
            </div>

            <div className="card flex flex-col items-center p-5 sm:p-6 xl:col-span-2">
              <div className="mb-2 w-full">
                <h2 className="font-display text-base font-bold text-slate-900">Savings rate</h2>
                <p className="text-xs text-slate-500">Share of income kept this period</p>
              </div>
              <div className="flex flex-1 items-center py-2">
                <SavingsRing percent={savingsRate} />
              </div>
              <p className="text-center text-xs text-slate-500">
                You kept <span className="font-bold text-slate-800">{formatCurrency(net)}</span> of{' '}
                {formatCurrency(income)} earned.
              </p>
            </div>
          </div>

          <div className="grid gap-6 xl:grid-cols-5">
            <div className="xl:col-span-3">
              <BudgetsCard
                budgets={budgets.data || []}
                loading={budgets.isLoading}
                onManage={() => setBudgetOpen(true)}
              />
            </div>
            <div className="xl:col-span-2">
              <InsightsCard insights={insights.data || []} loading={insights.isLoading} />
            </div>
          </div>

          <div className="grid gap-6 xl:grid-cols-5">
            <div className="card p-5 sm:p-6 xl:col-span-3">
              <div className="mb-5 flex items-center justify-between">
                <div>
                  <h2 className="font-display text-base font-bold text-slate-900">
                    Category breakdown
                  </h2>
                  <p className="text-xs text-slate-500">Hover a slice or row to inspect</p>
                </div>
                <BarChart3 className="h-5 w-5 text-slate-300" />
              </div>
              {summary.isLoading || !summary.data ? (
                <div className="skeleton h-[260px] w-full" />
              ) : donutData.length === 0 ? (
                <p className="py-16 text-center text-sm text-slate-400">
                  No expense data for this period.
                </p>
              ) : (
                <CategoryDonut data={donutData} />
              )}
            </div>

            <div className="card p-5 sm:p-6 xl:col-span-2">
              <div className="mb-5 flex items-center justify-between">
                <div>
                  <h2 className="font-display text-base font-bold text-slate-900">Top merchants</h2>
                  <p className="text-xs text-slate-500">By total amount spent</p>
                </div>
                <Store className="h-5 w-5 text-slate-300" />
              </div>
              {summary.isLoading || !summary.data ? (
                <div className="space-y-4">
                  {Array.from({ length: 5 }).map((_, index) => (
                    <div key={index} className="skeleton h-10" />
                  ))}
                </div>
              ) : summary.data.top_merchants.length === 0 ? (
                <p className="py-14 text-center text-sm text-slate-400">No merchant data yet.</p>
              ) : (
                <div className="space-y-4">
                  {summary.data.top_merchants.map((item) => (
                    <div key={item.name} className="group">
                      <div className="mb-1.5 flex items-center justify-between gap-3 text-sm">
                        <span className="flex min-w-0 items-center gap-2 font-semibold text-slate-700">
                          <MerchantAvatar name={item.name} size="sm" />
                          <span className="truncate">{item.name}</span>
                        </span>
                        <span className="shrink-0 font-bold tabular-nums text-slate-900">
                          {formatCompactCurrency(item.total)}
                        </span>
                      </div>
                      <div className="h-1.5 w-full overflow-hidden rounded-full bg-slate-100">
                        <div
                          className="h-full rounded-full bg-gradient-to-r from-indigo-500 to-violet-500 transition-all duration-700 group-hover:brightness-110"
                          style={{ width: `${Math.max((Number(item.total) / maxMerchant) * 100, 4)}%` }}
                        />
                      </div>
                      <p className="mt-1 text-[11px] text-slate-400">{item.count} transactions</p>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>

          <div className="grid gap-6 xl:grid-cols-5">
            <div className="card overflow-hidden xl:col-span-3">
              <div className="flex items-center justify-between border-b border-slate-100 px-5 py-4 sm:px-6">
                <div>
                  <h2 className="font-display text-base font-bold text-slate-900">
                    Recent transactions
                  </h2>
                  <p className="text-xs text-slate-500">Latest activity in this period</p>
                </div>
                <Link
                  to="/app/transactions"
                  className="flex items-center gap-1 text-xs font-bold text-indigo-600 transition hover:text-indigo-500"
                >
                  View all <ReceiptText className="h-3.5 w-3.5" />
                </Link>
              </div>
              {recent.isLoading || !recent.data ? (
                <div className="space-y-2 p-5">
                  {Array.from({ length: 5 }).map((_, index) => (
                    <div key={index} className="skeleton h-12" />
                  ))}
                </div>
              ) : recent.data.items.length === 0 ? (
                <p className="py-12 text-center text-sm text-slate-400">No transactions yet.</p>
              ) : (
                <ul className="divide-y divide-slate-100">
                  {recent.data.items.map((transaction) => (
                    <li
                      key={transaction.id}
                      className="flex items-center gap-4 px-5 py-3.5 transition hover:bg-slate-50/70 sm:px-6"
                    >
                      <CategoryIcon
                        name={transaction.category_name ?? 'Other'}
                        color={transaction.category_id ? colorById.get(transaction.category_id) : undefined}
                        size="md"
                      />
                      <div className="min-w-0 flex-1">
                        <p className="truncate text-sm font-semibold text-slate-800">
                          {transaction.description}
                        </p>
                        <p className="mt-0.5 flex items-center gap-2 text-xs text-slate-400">
                          <span>{formatDate(transaction.date)}</span>
                          <span className="h-1 w-1 rounded-full bg-slate-300" />
                          <span>{transaction.category_name ?? 'Uncategorized'}</span>
                        </p>
                      </div>
                      <div className="text-right">
                        <p
                          className={cn(
                            'text-sm font-bold tabular-nums',
                            transaction.type === 'DEBIT' ? 'text-slate-900' : 'text-emerald-600',
                          )}
                        >
                          {transaction.type === 'DEBIT' ? '−' : '+'}
                          {formatCurrency(transaction.amount, true)}
                        </p>
                        <p className="text-[11px] text-slate-400">
                          {transaction.type === 'DEBIT' ? 'Debit' : 'Credit'}
                        </p>
                      </div>
                    </li>
                  ))}
                </ul>
              )}
            </div>

            <div className="card overflow-hidden xl:col-span-2">
              <div className="border-b border-slate-100 px-5 py-4 sm:px-6">
                <h2 className="font-display text-base font-bold text-slate-900">Recent imports</h2>
                <p className="text-xs text-slate-500">Statement history</p>
              </div>
              {uploads.isLoading ? (
                <div className="space-y-2 p-5">
                  {Array.from({ length: 3 }).map((_, index) => (
                    <div key={index} className="skeleton h-12" />
                  ))}
                </div>
              ) : (uploads.data || []).length === 0 ? (
                <p className="py-12 text-center text-sm text-slate-400">No uploads yet.</p>
              ) : (
                <ul className="divide-y divide-slate-100">
                  {uploads.data!.slice(0, 5).map((item) => (
                    <li key={item.id} className="flex items-center gap-3 px-5 py-3.5 sm:px-6">
                      <span
                        className={cn(
                          'flex h-9 w-9 shrink-0 items-center justify-center rounded-xl',
                          item.status === 'COMPLETED'
                            ? 'bg-emerald-50 text-emerald-600'
                            : item.status === 'FAILED'
                              ? 'bg-rose-50 text-rose-600'
                              : 'bg-amber-50 text-amber-600',
                        )}
                      >
                        {item.status === 'COMPLETED' ? (
                          <CheckCircle2 className="h-4 w-4" />
                        ) : item.status === 'FAILED' ? (
                          <XCircle className="h-4 w-4" />
                        ) : (
                          <AlertTriangle className="h-4 w-4" />
                        )}
                      </span>
                      <div className="min-w-0 flex-1">
                        <p className="truncate text-sm font-semibold text-slate-800">
                          {item.filename}
                        </p>
                        <p className="text-[11px] text-slate-400">
                          {formatDateTimeSafe(item.created_at)}
                        </p>
                      </div>
                      <div className="text-right">
                        <Badge
                          tone={
                            item.status === 'COMPLETED'
                              ? 'emerald'
                              : item.status === 'FAILED'
                                ? 'rose'
                                : 'amber'
                          }
                        >
                          {item.imported_count} in
                        </Badge>
                        <p className="mt-1 text-[11px] text-slate-400">{item.duplicate_count} dup</p>
                      </div>
                    </li>
                  ))}
                </ul>
              )}
            </div>
          </div>
        </>
      )}

      <BudgetModal
        open={budgetOpen}
        onClose={() => setBudgetOpen(false)}
        categories={categories.data || []}
        budgets={budgets.data || []}
      />
    </div>
  )
}
