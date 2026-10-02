import { useEffect, useState } from 'react'
import { createPortal } from 'react-dom'
import { useQueryClient } from '@tanstack/react-query'
import { X } from 'lucide-react'
import { CategoryIcon } from './CategoryIcon'
import { Button } from './ui/Button'
import { useToast } from '../context/ToastContext'
import { api } from '../lib/api'
import type { Budget, Category } from '../lib/types'

export function BudgetModal({
  open,
  onClose,
  categories,
  budgets,
}: {
  open: boolean
  onClose: () => void
  categories: Category[]
  budgets: Budget[]
}) {
  const queryClient = useQueryClient()
  const toast = useToast()
  const [values, setValues] = useState<Record<number, string>>({})
  const [busy, setBusy] = useState(false)

  useEffect(() => {
    if (!open) return
    const initial: Record<number, string> = {}
    budgets.forEach((b) => {
      initial[b.category_id] = String(Number(b.limit))
    })
    setValues(initial)
  }, [open, budgets])

  useEffect(() => {
    if (!open) return
    const onKey = (event: KeyboardEvent) => {
      if (event.key === 'Escape') onClose()
    }
    document.addEventListener('keydown', onKey)
    return () => document.removeEventListener('keydown', onKey)
  }, [open, onClose])

  if (!open) return null

  const save = async () => {
    setBusy(true)
    try {
      const existing = new Map(budgets.map((b) => [b.category_id, b]))
      const ops: Promise<unknown>[] = []
      for (const category of categories) {
        const raw = (values[category.id] ?? '').trim()
        const amount = Number(raw)
        const current = existing.get(category.id)
        if (raw && amount > 0) {
          if (!current || Number(current.limit) !== amount) {
            ops.push(
              api(`/api/budgets/${category.id}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ amount: amount.toFixed(2) }),
              }),
            )
          }
        } else if (current) {
          ops.push(api(`/api/budgets/${category.id}`, { method: 'DELETE' }))
        }
      }
      await Promise.all(ops)
      queryClient.invalidateQueries({ queryKey: ['budgets'] })
      toast.success('Budgets saved')
      onClose()
    } catch (error) {
      toast.error('Could not save budgets', (error as Error).message)
    } finally {
      setBusy(false)
    }
  }

  return createPortal(
    <div className="fixed inset-0 z-[100] flex items-end justify-center bg-ink-950/50 backdrop-blur-sm animate-fade-in sm:items-center sm:p-6">
      <div className="flex max-h-[90vh] w-full max-w-lg flex-col rounded-t-3xl border border-slate-200 bg-white shadow-pop animate-scale-in sm:rounded-3xl">
        <div className="flex items-center justify-between border-b border-slate-100 px-5 py-4">
          <div>
            <h3 className="font-display text-base font-bold text-slate-900">Category budgets</h3>
            <p className="text-xs text-slate-500">
              Set a limit for the selected period. Leave blank for no budget.
            </p>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="rounded-lg p-2 text-slate-400 transition hover:bg-slate-100 hover:text-slate-600"
            aria-label="Close"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        <div className="flex-1 overflow-y-auto px-5 py-4">
          <div className="space-y-2">
            {categories.map((category) => (
              <div key={category.id} className="flex items-center gap-3">
                <CategoryIcon name={category.name} color={category.color} size="sm" />
                <span className="flex-1 truncate text-sm font-semibold text-slate-700">
                  {category.name}
                </span>
                <div className="relative">
                  <span className="pointer-events-none absolute left-2.5 top-1/2 -translate-y-1/2 text-xs text-slate-400">
                    ₹
                  </span>
                  <input
                    type="number"
                    min="0"
                    step="100"
                    inputMode="decimal"
                    value={values[category.id] ?? ''}
                    onChange={(event) =>
                      setValues((current) => ({ ...current, [category.id]: event.target.value }))
                    }
                    placeholder="—"
                    className="h-9 w-32 rounded-lg border border-slate-200 bg-white pl-6 pr-2 text-right text-sm font-semibold text-slate-800 outline-none transition focus:border-indigo-400 focus:ring-2 focus:ring-indigo-500/10"
                  />
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="flex items-center justify-end gap-2 border-t border-slate-100 px-5 py-4">
          <Button variant="secondary" onClick={onClose}>
            Cancel
          </Button>
          <Button onClick={save} loading={busy}>
            Save budgets
          </Button>
        </div>
      </div>
    </div>,
    document.body,
  )
}
