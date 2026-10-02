import type { LucideIcon } from 'lucide-react'
import type { ReactNode } from 'react'

export function EmptyState({
  icon: Icon,
  title,
  description,
  action,
}: {
  icon: LucideIcon
  title: string
  description: string
  action?: ReactNode
}) {
  return (
    <div className="flex flex-col items-center justify-center px-6 py-14 text-center animate-fade-in">
      <div className="relative mb-5">
        <div className="absolute inset-0 -z-10 scale-150 rounded-full bg-gradient-to-br from-indigo-100 via-violet-100 to-fuchsia-100 blur-xl" />
        <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-gradient-to-br from-indigo-500 to-violet-600 shadow-lg shadow-indigo-500/25">
          <Icon className="h-7 w-7 text-white" />
        </div>
      </div>
      <h3 className="font-display text-base font-bold text-slate-900">{title}</h3>
      <p className="mt-1.5 max-w-sm text-sm leading-relaxed text-slate-500">{description}</p>
      {action ? <div className="mt-6">{action}</div> : null}
    </div>
  )
}
