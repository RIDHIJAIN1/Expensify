import { useEffect, useRef, useState } from 'react'
import { CalendarRange, Check, ChevronDown } from 'lucide-react'
import { cn } from '../lib/cn'
import { formatDate, formatDateInput } from '../lib/format'
import type { DateRange } from '../lib/types'

const PRESETS = [
  { label: '30D', months: 0, days: 30 },
  { label: '3M', months: 3, days: 0 },
  { label: '6M', months: 6, days: 0 },
  { label: '1Y', months: 12, days: 0 },
]

export function presetRange(months: number, days: number): DateRange {
  const to = new Date()
  const from = new Date()
  if (days) from.setDate(from.getDate() - days)
  else from.setMonth(from.getMonth() - months)
  return { from: formatDateInput(from), to: formatDateInput(to) }
}

export function DateRangePicker({
  value,
  onChange,
  className,
}: {
  value: DateRange
  onChange: (range: DateRange) => void
  className?: string
}) {
  const [open, setOpen] = useState(false)
  const [draft, setDraft] = useState(value)
  const ref = useRef<HTMLDivElement>(null)

  useEffect(() => {
    setDraft(value)
  }, [value])

  useEffect(() => {
    if (!open) return
    const onDown = (event: MouseEvent) => {
      if (ref.current && !ref.current.contains(event.target as Node)) setOpen(false)
    }
    document.addEventListener('mousedown', onDown)
    return () => document.removeEventListener('mousedown', onDown)
  }, [open])

  const activePreset = PRESETS.find((preset) => {
    const range = presetRange(preset.months, preset.days)
    return range.from === value.from && range.to === value.to
  })

  const apply = (range: DateRange) => {
    onChange(range)
    setOpen(false)
  }

  return (
    <div ref={ref} className={cn('relative', className)}>
      <button
        type="button"
        onClick={() => setOpen((current) => !current)}
        className="inline-flex h-10 items-center gap-2 rounded-xl border border-slate-200 bg-white px-3.5 text-sm font-semibold text-slate-700 shadow-sm transition hover:border-slate-300 hover:bg-slate-50"
      >
        <CalendarRange className="h-4 w-4 text-indigo-500" />
        <span className="hidden sm:inline">
          {formatDate(value.from)} – {formatDate(value.to)}
        </span>
        <span className="sm:hidden">{activePreset?.label ?? 'Custom'}</span>
        <ChevronDown className={cn('h-3.5 w-3.5 text-slate-400 transition', open && 'rotate-180')} />
      </button>

      {open ? (
        <div className="absolute right-0 z-40 mt-2 w-72 rounded-2xl border border-slate-200 bg-white p-4 shadow-pop animate-scale-in">
          <p className="mb-2 text-[11px] font-bold uppercase tracking-wider text-slate-400">
            Quick ranges
          </p>
          <div className="grid grid-cols-4 gap-1.5">
            {PRESETS.map((preset) => {
              const isActive = activePreset?.label === preset.label
              return (
                <button
                  key={preset.label}
                  type="button"
                  onClick={() => apply(presetRange(preset.months, preset.days))}
                  className={cn(
                    'relative rounded-lg border py-1.5 text-xs font-bold transition',
                    isActive
                      ? 'border-indigo-600 bg-indigo-600 text-white'
                      : 'border-slate-200 text-slate-600 hover:border-indigo-300 hover:text-indigo-600',
                  )}
                >
                  {preset.label}
                  {isActive ? <Check className="absolute right-1 top-1 h-2.5 w-2.5" /> : null}
                </button>
              )
            })}
          </div>

          <p className="mb-2 mt-4 text-[11px] font-bold uppercase tracking-wider text-slate-400">
            Custom
          </p>
          <div className="grid grid-cols-2 gap-2">
            <label className="block">
              <span className="mb-1 block text-[11px] font-medium text-slate-500">From</span>
              <input
                type="date"
                value={draft.from}
                max={draft.to}
                onChange={(e) => setDraft((current) => ({ ...current, from: e.target.value }))}
                className="h-9 w-full rounded-lg border border-slate-200 px-2.5 text-xs text-slate-700 outline-none focus:border-indigo-400 focus:ring-2 focus:ring-indigo-500/10"
              />
            </label>
            <label className="block">
              <span className="mb-1 block text-[11px] font-medium text-slate-500">To</span>
              <input
                type="date"
                value={draft.to}
                min={draft.from}
                max={formatDateInput(new Date())}
                onChange={(e) => setDraft((current) => ({ ...current, to: e.target.value }))}
                className="h-9 w-full rounded-lg border border-slate-200 px-2.5 text-xs text-slate-700 outline-none focus:border-indigo-400 focus:ring-2 focus:ring-indigo-500/10"
              />
            </label>
          </div>
          <button
            type="button"
            onClick={() => draft.from && draft.to && apply(draft)}
            className="mt-3 h-9 w-full rounded-lg bg-gradient-to-r from-indigo-600 to-violet-600 text-xs font-bold text-white transition hover:from-indigo-500 hover:to-violet-500"
          >
            Apply custom range
          </button>
        </div>
      ) : null}
    </div>
  )
}
