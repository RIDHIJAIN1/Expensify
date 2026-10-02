import type { ReactNode } from 'react'
import { cn } from '../../lib/cn'

type Tone = 'indigo' | 'emerald' | 'rose' | 'amber' | 'slate' | 'violet' | 'sky'

const TONES: Record<Tone, string> = {
  indigo: 'bg-indigo-50 text-indigo-700 ring-indigo-600/10',
  emerald: 'bg-emerald-50 text-emerald-700 ring-emerald-600/10',
  rose: 'bg-rose-50 text-rose-700 ring-rose-600/10',
  amber: 'bg-amber-50 text-amber-700 ring-amber-600/10',
  slate: 'bg-slate-100 text-slate-600 ring-slate-500/10',
  violet: 'bg-violet-50 text-violet-700 ring-violet-600/10',
  sky: 'bg-sky-50 text-sky-700 ring-sky-600/10',
}

export function Badge({
  tone = 'slate',
  children,
  className,
}: {
  tone?: Tone
  children: ReactNode
  className?: string
}) {
  return (
    <span
      className={cn(
        'inline-flex items-center gap-1 rounded-full px-2.5 py-1 text-[11px] font-semibold ring-1 ring-inset',
        TONES[tone],
        className,
      )}
    >
      {children}
    </span>
  )
}
