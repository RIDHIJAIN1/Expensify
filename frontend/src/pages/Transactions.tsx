import { useMemo, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { FileSpreadsheet, FileText, Search } from 'lucide-react'
import { DateRangePicker, presetRange } from '../components/DateRangePicker'
import { CategoryIcon } from '../components/CategoryIcon'
import { Badge } from '../components/ui/Badge'
import { Button } from '../components/ui/Button'
import { Select, type SelectOption } from '../components/ui/Select'
import { useToast } from '../context/ToastContext'
import { api, download } from '../lib/api'
import { cn } from '../lib/cn'
import { formatCurrency, formatDate } from '../lib/format'
import type { Category, DateRange, Transaction, TransactionList, TransactionUpdateResult } from '../lib/types'

const LIMIT = 25

function Dot({ color }: { color?: string | null }) {
  return (
    <span
      className="h-2.5 w-2.5 shrink-0 rounded-full"
      style={{ backgroundColor: color || '#94a3b8' }}
    />
  )
}

export default function Transactions() {
  const [range, setRange] = useState<DateRange>(() => presetRange(6, 0))
  const [category, setCategory] = useState<number | ''>('')
  const [search, setSearch] = useState('')
  const [page, setPage] = useState(0)
  const queryClient = useQueryClient()
  const toast = useToast()

  const params = useMemo(() => {
    const p = new URLSearchParams({
      date_from: range.from,
      date_to: range.to,
      limit: String(LIMIT),
      offset: String(page * LIMIT),
    })
    if (category) p.set('category_id', String(category))
    if (search.trim()) p.set('search', search.trim())
    return p
  }, [range, category, search, page])

  const txQuery = useQuery({
    queryKey: ['transactions', params.toString()],
    queryFn: () => api<TransactionList>(`/api/transactions?${params.toString()}`),
  })

  const catQuery = useQuery({
    queryKey: ['categories'],
    queryFn: () => api<Category[]>('/api/categories'),
  })

  const colorById = useMemo(() => {
    const map = new Map<number, string>()
    ;(catQuery.data || []).forEach((c) => {
      if (c.color) map.set(c.id, c.color)
    })
    return map
  }, [catQuery.data])

  const categoryOptions: SelectOption[] = useMemo(
    () => [
      { value: '', label: 'Uncategorized', icon: <Dot /> },
      ...(catQuery.data || []).map((c) => ({
        value: String(c.id),
        label: c.name,
        icon: <Dot color={c.color} />,
      })),
    ],
    [catQuery.data],
  )

  const filterOptions: SelectOption[] = useMemo(
    () => [
      { value: '', label: 'All categories', icon: <Dot color="#cbd5e1" /> },
      ...(catQuery.data || []).map((c) => ({
        value: String(c.id),
        label: c.name,
        icon: <Dot color={c.color} />,
      })),
    ],
    [catQuery.data],
  )

  const reCat = useMutation({
    mutationFn: ({ id, category_id }: { id: number; category_id: number | null }) =>
      api<TransactionUpdateResult>(`/api/transactions/${id}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ category_id }),
      }),
    onSuccess: (result) => {
      queryClient.invalidateQueries({ queryKey: ['transactions'] })
      queryClient.invalidateQueries({ queryKey: ['summary'] })
      queryClient.invalidateQueries({ queryKey: ['categories'] })
      queryClient.invalidateQueries({ queryKey: ['insights'] })
      if (result.learned_keyword) {
        toast.success(
          'Category updated',
          `Learned “${result.learned_keyword}”${
            result.reclassified ? ` · ${result.reclassified} more updated` : ''
          }`,
        )
      } else {
        toast.success('Transaction updated')
      }
    },
  })

  const total = txQuery.data?.total || 0
  const pages = Math.max(1, Math.ceil(total / LIMIT))
  const items = txQuery.data?.items ?? []

  const exportData = async (kind: 'csv' | 'pdf') => {
    const p = new URLSearchParams({ date_from: range.from, date_to: range.to })
    if (category) p.set('category_id', String(category))
    try {
      await download(`/api/export/${kind}?${p.toString()}`, `expenses.${kind}`)
      toast.success(`${kind.toUpperCase()} downloaded`)
    } catch {
      toast.error('Export failed')
    }
  }

  const renderCategorySelect = (t: Transaction, wrapperClass: string) => (
    <Select
      value={t.category_id ? String(t.category_id) : ''}
      onChange={(value) =>
        reCat.mutate({ id: t.id, category_id: value ? Number(value) : null })
      }
      options={categoryOptions}
      size="sm"
      className={wrapperClass}
    />
  )

  return (
    <div className="space-y-6 animate-fade-up">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
        <div>
          <h1 className="font-display text-2xl font-extrabold tracking-tight text-slate-900">
            Transactions
          </h1>
          <p className="mt-1 text-sm text-slate-500">Review and re-categorize every line.</p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <Button
            variant="secondary"
            icon={<FileSpreadsheet className="h-3.5 w-3.5" />}
            onClick={() => exportData('csv')}
          >
            CSV
          </Button>
          <Button variant="dark" icon={<FileText className="h-3.5 w-3.5" />} onClick={() => exportData('pdf')}>
            PDF
          </Button>
        </div>
      </div>

      <div className="card flex flex-col gap-3 p-4 sm:flex-row sm:flex-wrap sm:items-center">
        <DateRangePicker value={range} onChange={(r) => { setRange(r); setPage(0) }} />
        <Select
          value={category ? String(category) : ''}
          onChange={(value) => {
            setCategory(value ? Number(value) : '')
            setPage(0)
          }}
          options={filterOptions}
          className="w-full sm:w-48"
        />
        <div className="relative sm:ml-auto">
          <Search className="pointer-events-none absolute left-3.5 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
          <input
            value={search}
            onChange={(e) => {
              setSearch(e.target.value)
              setPage(0)
            }}
            placeholder="Search description…"
            className="h-10 w-full rounded-xl border border-slate-200 bg-white pl-10 pr-3 text-sm text-slate-800 shadow-sm outline-none transition placeholder:text-slate-400 focus:border-indigo-400 focus:ring-4 focus:ring-indigo-500/10 sm:w-72"
          />
        </div>
      </div>

      <div className="card overflow-hidden">
        {txQuery.isLoading ? (
          <div className="space-y-3 p-4">
            {Array.from({ length: 6 }).map((_, index) => (
              <div key={index} className="skeleton h-12" />
            ))}
          </div>
        ) : items.length === 0 ? (
          <p className="py-14 text-center text-sm text-slate-400">
            No transactions found for these filters.
          </p>
        ) : (
          <>
            {/* Desktop table */}
            <div className="hidden md:block">
              <table className="w-full text-left text-sm">
                <thead>
                  <tr className="border-b border-slate-100 bg-slate-50/60 text-[11px] font-bold uppercase tracking-wider text-slate-400">
                    <th className="px-5 py-3.5">Merchant</th>
                    <th className="px-5 py-3.5">Date</th>
                    <th className="px-5 py-3.5">Type</th>
                    <th className="px-5 py-3.5">Category</th>
                    <th className="px-5 py-3.5 text-right">Amount</th>
                  </tr>
                </thead>
                <tbody>
                  {items.map((t) => (
                    <tr
                      key={t.id}
                      className="border-b border-slate-100 last:border-0 hover:bg-slate-50/60"
                    >
                      <td className="px-5 py-3.5">
                        <div className="flex items-center gap-3">
                          <CategoryIcon
                            name={t.category_name ?? 'Other'}
                            color={t.category_id ? colorById.get(t.category_id) : undefined}
                            size="sm"
                          />
                          <span className="font-semibold text-slate-800">{t.description}</span>
                        </div>
                      </td>
                      <td className="whitespace-nowrap px-5 py-3.5 text-slate-500">
                        {formatDate(t.date)}
                      </td>
                      <td className="px-5 py-3.5">
                        <Badge tone={t.type === 'CREDIT' ? 'emerald' : 'rose'}>
                          {t.type === 'CREDIT' ? 'Credit' : 'Debit'}
                        </Badge>
                      </td>
                      <td className="px-5 py-3.5">{renderCategorySelect(t, 'w-44')}</td>
                      <td
                        className={cn(
                          'whitespace-nowrap px-5 py-3.5 text-right font-bold tabular-nums',
                          t.type === 'CREDIT' ? 'text-emerald-600' : 'text-slate-900',
                        )}
                      >
                        {t.type === 'DEBIT' ? '−' : '+'}
                        {formatCurrency(t.amount, true)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Mobile cards */}
            <ul className="divide-y divide-slate-100 md:hidden">
              {items.map((t) => (
                <li key={t.id} className="p-4">
                  <div className="flex items-start gap-3">
                    <CategoryIcon
                      name={t.category_name ?? 'Other'}
                      color={t.category_id ? colorById.get(t.category_id) : undefined}
                      size="sm"
                    />
                    <div className="min-w-0 flex-1">
                      <p className="truncate text-sm font-semibold text-slate-800">
                        {t.description}
                      </p>
                      <p className="mt-0.5 flex flex-wrap items-center gap-x-2 text-xs text-slate-400">
                        <span>{formatDate(t.date)}</span>
                        <span className="h-1 w-1 rounded-full bg-slate-300" />
                        <span>{t.category_name ?? 'Uncategorized'}</span>
                      </p>
                    </div>
                    <div className="shrink-0 text-right">
                      <p
                        className={cn(
                          'text-sm font-bold tabular-nums',
                          t.type === 'CREDIT' ? 'text-emerald-600' : 'text-slate-900',
                        )}
                      >
                        {t.type === 'DEBIT' ? '−' : '+'}
                        {formatCurrency(t.amount, true)}
                      </p>
                      <span className="text-[11px] text-slate-400">
                        {t.type === 'CREDIT' ? 'Credit' : 'Debit'}
                      </span>
                    </div>
                  </div>
                  <div className="mt-3">{renderCategorySelect(t, 'w-full')}</div>
                </li>
              ))}
            </ul>
          </>
        )}
      </div>

      <div className="flex items-center justify-between text-sm text-slate-500">
        <span className="font-medium">
          {total} transaction{total === 1 ? '' : 's'}
        </span>
        <div className="flex items-center gap-2">
          <Button variant="secondary" size="sm" disabled={page === 0} onClick={() => setPage((p) => p - 1)}>
            Previous
          </Button>
          <span className="px-1 font-semibold tabular-nums">
            {page + 1} / {pages}
          </span>
          <Button
            variant="secondary"
            size="sm"
            disabled={page + 1 >= pages}
            onClick={() => setPage((p) => p + 1)}
          >
            Next
          </Button>
        </div>
      </div>
    </div>
  )
}
