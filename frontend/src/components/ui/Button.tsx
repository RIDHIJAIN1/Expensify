import type { ButtonHTMLAttributes, ReactNode } from 'react'
import { Loader2 } from 'lucide-react'
import { cn } from '../../lib/cn'

type Variant = 'primary' | 'secondary' | 'ghost' | 'danger' | 'dark'
type Size = 'sm' | 'md' | 'lg'

type ButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: Variant
  size?: Size
  loading?: boolean
  icon?: ReactNode
}

const VARIANTS: Record<Variant, string> = {
  primary:
    'bg-gradient-to-r from-indigo-600 to-violet-600 text-white shadow-sm shadow-indigo-600/25 hover:from-indigo-500 hover:to-violet-500 active:from-indigo-700 active:to-violet-700 disabled:from-indigo-300 disabled:to-violet-300',
  secondary:
    'border border-slate-200 bg-white text-slate-700 shadow-sm hover:border-slate-300 hover:bg-slate-50 active:bg-slate-100 disabled:text-slate-400',
  ghost: 'text-slate-600 hover:bg-slate-100 hover:text-slate-900 disabled:text-slate-300',
  danger:
    'bg-rose-600 text-white shadow-sm shadow-rose-600/25 hover:bg-rose-500 active:bg-rose-700 disabled:bg-rose-300',
  dark: 'bg-ink-900 text-white hover:bg-ink-800 active:bg-ink-950 disabled:bg-slate-400',
}

const SIZES: Record<Size, string> = {
  sm: 'h-8 px-3 text-xs gap-1.5 rounded-lg',
  md: 'h-10 px-4 text-sm gap-2 rounded-xl',
  lg: 'h-12 px-6 text-sm gap-2 rounded-xl',
}

export function Button({
  variant = 'primary',
  size = 'md',
  loading = false,
  icon,
  className,
  children,
  disabled,
  ...rest
}: ButtonProps) {
  return (
    <button
      className={cn(
        'inline-flex select-none items-center justify-center font-semibold transition-all duration-150 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-500/50 focus-visible:ring-offset-2 disabled:cursor-not-allowed',
        VARIANTS[variant],
        SIZES[size],
        className,
      )}
      disabled={disabled || loading}
      {...rest}
    >
      {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : icon}
      {children}
    </button>
  )
}
