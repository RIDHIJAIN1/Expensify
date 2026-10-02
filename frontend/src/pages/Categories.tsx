import { useState, type FormEvent } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Plus, Trash2 } from 'lucide-react'
import { CategoryIcon } from '../components/CategoryIcon'
import { Badge } from '../components/ui/Badge'
import { Button } from '../components/ui/Button'
import { Input } from '../components/ui/Input'
import { useToast } from '../context/ToastContext'
import { api } from '../lib/api'
import type { Category } from '../lib/types'

export default function Categories() {
  const queryClient = useQueryClient()
  const toast = useToast()
  const [name, setName] = useState('')
  const [keywords, setKeywords] = useState('')
  const [color, setColor] = useState('#4f46e5')

  const q = useQuery({
    queryKey: ['categories'],
    queryFn: () => api<Category[]>('/api/categories'),
  })

  const add = useMutation({
    mutationFn: (body: { name: string; keywords: string[]; color: string }) =>
      api('/api/categories', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['categories'] })
      setName('')
      setKeywords('')
      toast.success('Category added')
    },
    onError: (e) => toast.error('Could not add category', (e as Error).message),
  })

  const del = useMutation({
    mutationFn: (id: number) => api(`/api/categories/${id}`, { method: 'DELETE' }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['categories'] })
      queryClient.invalidateQueries({ queryKey: ['summary'] })
      queryClient.invalidateQueries({ queryKey: ['transactions'] })
      toast.success('Category removed')
    },
  })

  function handleSubmit(e: FormEvent) {
    e.preventDefault()
    if (!name.trim()) return
    add.mutate({
      name: name.trim(),
      keywords: keywords
        .split(',')
        .map((k) => k.trim())
        .filter(Boolean),
      color,
    })
  }

  return (
    <div className="space-y-6 animate-fade-up">
      <div>
        <h1 className="font-display text-2xl font-extrabold tracking-tight text-slate-900">
          Categories
        </h1>
        <p className="mt-1 text-sm text-slate-500">
          Add keywords so the classifier recognizes your merchants automatically.
        </p>
      </div>

      <form onSubmit={handleSubmit} className="card p-5 sm:p-6">
        <div className="grid grid-cols-1 gap-4 md:grid-cols-[1fr_2fr_auto_auto] md:items-end">
          <Input
            label="Category name"
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="e.g. Fitness"
            required
          />
          <Input
            label="Keywords (comma-separated)"
            value={keywords}
            onChange={(e) => setKeywords(e.target.value)}
            placeholder="gym, cult, fitness, yoga"
          />
          <div>
            <label className="mb-1.5 block text-xs font-semibold uppercase tracking-wide text-slate-500">
              Color
            </label>
            <input
              type="color"
              value={color}
              onChange={(e) => setColor(e.target.value)}
              className="h-11 w-14 cursor-pointer rounded-xl border border-slate-200 bg-white p-1"
            />
          </div>
          <Button type="submit" icon={<Plus className="h-4 w-4" />} loading={add.isPending}>
            Add
          </Button>
        </div>
      </form>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {(q.data || []).map((c) => (
          <div key={c.id} className="card group relative overflow-hidden p-5 transition-shadow hover:shadow-pop">
            <div className="flex items-start justify-between">
              <div className="flex items-center gap-3">
                <CategoryIcon name={c.name} color={c.color} size="md" />
                <div>
                  <p className="font-display text-sm font-bold text-slate-900">{c.name}</p>
                  <p className="text-[10px] font-semibold uppercase tracking-wider text-slate-400">
                    {c.is_custom ? 'Custom' : 'Default'}
                  </p>
                </div>
              </div>
              {c.is_custom ? (
                <button
                  type="button"
                  onClick={() => del.mutate(c.id)}
                  title="Delete category"
                  className="rounded-lg p-2 text-slate-300 opacity-0 transition hover:bg-rose-50 hover:text-rose-500 group-hover:opacity-100"
                >
                  <Trash2 className="h-4 w-4" />
                </button>
              ) : (
                <Badge tone="slate">Seeded</Badge>
              )}
            </div>

            <div className="mt-4 flex flex-wrap gap-1.5">
              {c.keywords.length > 0 ? (
                c.keywords.slice(0, 6).map((k) => (
                  <span key={k} className="rounded-md bg-slate-100 px-2 py-0.5 text-xs text-slate-600">
                    {k}
                  </span>
                ))
              ) : (
                <span className="text-xs text-slate-400">Fallback bucket — no keywords</span>
              )}
              {c.keywords.length > 6 && (
                <span className="rounded-md bg-slate-100 px-2 py-0.5 text-xs text-slate-500">
                  +{c.keywords.length - 6}
                </span>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
