import type { ComponentPropsWithRef, ReactNode } from 'react'
import { cn } from '../../lib/cn'

type InputProps = ComponentPropsWithRef<'input'> & {
  label?: string
  error?: string
  hint?: string
  icon?: ReactNode
}

export function Input({ label, error, hint, icon, className, id, ...rest }: InputProps) {
  const inputId = id ?? rest.name
  return (
    <div className="w-full">
      {label ? (
        <label
          htmlFor={inputId}
          className="mb-1.5 block text-xs font-semibold uppercase tracking-wide text-slate-500"
        >
          {label}
        </label>
      ) : null}
      <div className="relative">
        {icon ? (
          <span className="pointer-events-none absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400">
            {icon}
          </span>
        ) : null}
        <input
          id={inputId}
          className={cn(
            'h-11 w-full rounded-xl border bg-white px-3.5 text-sm text-slate-900 shadow-sm outline-none transition placeholder:text-slate-400',
            'focus:border-indigo-400 focus:ring-4 focus:ring-indigo-500/10',
            icon ? 'pl-10' : '',
            error
              ? 'border-rose-300 focus:border-rose-400 focus:ring-rose-500/10'
              : 'border-slate-200',
            className,
          )}
          {...rest}
        />
      </div>
      {error ? <p className="mt-1.5 text-xs font-medium text-rose-600">{error}</p> : null}
      {!error && hint ? <p className="mt-1.5 text-xs text-slate-400">{hint}</p> : null}
    </div>
  )
}
