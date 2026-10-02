import { useEffect, useRef, useState, type ReactNode } from 'react'
import { createPortal } from 'react-dom'
import { Check, ChevronDown } from 'lucide-react'
import { cn } from '../../lib/cn'

export interface SelectOption {
  value: string
  label: string
  icon?: ReactNode
}

export function Select({
  value,
  onChange,
  options,
  placeholder = 'Select…',
  size = 'md',
  className,
  buttonClassName,
}: {
  value: string
  onChange: (value: string) => void
  options: SelectOption[]
  placeholder?: string
  size?: 'sm' | 'md'
  className?: string
  buttonClassName?: string
}) {
  const [open, setOpen] = useState(false)
  const [pos, setPos] = useState<{ top: number; left: number; width: number } | null>(null)
  const btnRef = useRef<HTMLButtonElement>(null)
  const panelRef = useRef<HTMLDivElement>(null)

  const selected = options.find((option) => option.value === value)

  function openMenu() {
    const el = btnRef.current
    if (!el) return
    const rect = el.getBoundingClientRect()
    const width = Math.max(rect.width, 210)
    const maxLeft = window.innerWidth - width - 12
    setPos({
      top: rect.bottom + 6,
      left: Math.max(12, Math.min(rect.left, Math.max(12, maxLeft))),
      width,
    })
    setOpen(true)
  }

  useEffect(() => {
    if (!open) return
    const onPointerDown = (event: MouseEvent) => {
      const target = event.target as Node
      if (btnRef.current?.contains(target) || panelRef.current?.contains(target)) return
      setOpen(false)
    }
    const onKey = (event: KeyboardEvent) => {
      if (event.key === 'Escape') setOpen(false)
    }
    const onScrollOrResize = () => setOpen(false)
    document.addEventListener('mousedown', onPointerDown)
    document.addEventListener('keydown', onKey)
    window.addEventListener('scroll', onScrollOrResize, true)
    window.addEventListener('resize', onScrollOrResize)
    return () => {
      document.removeEventListener('mousedown', onPointerDown)
      document.removeEventListener('keydown', onKey)
      window.removeEventListener('scroll', onScrollOrResize, true)
      window.removeEventListener('resize', onScrollOrResize)
    }
  }, [open])

  return (
    <div className={cn('relative', className)}>
      <button
        ref={btnRef}
        type="button"
        onClick={() => (open ? setOpen(false) : openMenu())}
        className={cn(
          'flex w-full items-center gap-2 rounded-lg border border-slate-200 bg-white font-semibold text-slate-700 shadow-sm outline-none transition hover:border-slate-300 focus:border-indigo-400 focus:ring-2 focus:ring-indigo-500/10',
          size === 'sm' ? 'h-9 px-2.5 text-xs' : 'h-10 px-3 text-sm',
          buttonClassName,
        )}
      >
        {selected?.icon}
        <span className="flex-1 truncate text-left">{selected?.label ?? placeholder}</span>
        <ChevronDown
          className={cn('h-3.5 w-3.5 shrink-0 text-slate-400 transition', open && 'rotate-180')}
        />
      </button>

      {open && pos
        ? createPortal(
            <div
              ref={panelRef}
              style={{ position: 'fixed', top: pos.top, left: pos.left, width: pos.width, zIndex: 80 }}
              className="max-h-72 overflow-y-auto rounded-xl border border-slate-200 bg-white p-1 shadow-pop animate-scale-in"
            >
              {options.map((option) => {
                const active = option.value === value
                return (
                  <button
                    key={option.value}
                    type="button"
                    onClick={() => {
                      onChange(option.value)
                      setOpen(false)
                    }}
                    className={cn(
                      'flex w-full items-center gap-2.5 rounded-lg px-2.5 py-2 text-sm transition',
                      active
                        ? 'bg-indigo-50 font-semibold text-indigo-700'
                        : 'text-slate-700 hover:bg-slate-50',
                    )}
                  >
                    {option.icon}
                    <span className="flex-1 truncate text-left">{option.label}</span>
                    {active ? <Check className="h-4 w-4 shrink-0 text-indigo-600" /> : null}
                  </button>
                )
              })}
            </div>,
            document.body,
          )
        : null}
    </div>
  )
}
