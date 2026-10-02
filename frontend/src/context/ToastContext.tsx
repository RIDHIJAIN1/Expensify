import {
  createContext,
  useCallback,
  useContext,
  useMemo,
  useRef,
  useState,
  type ReactNode,
} from 'react'
import { AlertTriangle, CheckCircle2, Info, X } from 'lucide-react'
import { cn } from '../lib/cn'

type ToastKind = 'success' | 'error' | 'info'

type Toast = {
  id: number
  kind: ToastKind
  title: string
  message?: string
}

type ToastContextValue = {
  toast: (kind: ToastKind, title: string, message?: string) => void
  success: (title: string, message?: string) => void
  error: (title: string, message?: string) => void
}

const ToastContext = createContext<ToastContextValue | null>(null)

const STYLES: Record<ToastKind, { icon: typeof Info; ring: string; iconColor: string }> = {
  success: { icon: CheckCircle2, ring: 'ring-emerald-200', iconColor: 'text-emerald-500' },
  error: { icon: AlertTriangle, ring: 'ring-rose-200', iconColor: 'text-rose-500' },
  info: { icon: Info, ring: 'ring-indigo-200', iconColor: 'text-indigo-500' },
}

export function ToastProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([])
  const idRef = useRef(0)

  const dismiss = useCallback((id: number) => {
    setToasts((current) => current.filter((item) => item.id !== id))
  }, [])

  const toast = useCallback(
    (kind: ToastKind, title: string, message?: string) => {
      const id = ++idRef.current
      setToasts((current) => [...current.slice(-3), { id, kind, title, message }])
      window.setTimeout(() => dismiss(id), kind === 'error' ? 6500 : 4200)
    },
    [dismiss],
  )

  const value = useMemo<ToastContextValue>(
    () => ({
      toast,
      success: (title, message) => toast('success', title, message),
      error: (title, message) => toast('error', title, message),
    }),
    [toast],
  )

  return (
    <ToastContext.Provider value={value}>
      {children}
      <div className="pointer-events-none fixed bottom-5 right-5 z-[100] flex w-full max-w-sm flex-col gap-3">
        {toasts.map((item) => {
          const style = STYLES[item.kind]
          const Icon = style.icon
          return (
            <div
              key={item.id}
              className={cn(
                'pointer-events-auto flex items-start gap-3 rounded-xl border border-slate-200 bg-white/95 p-4 shadow-pop ring-1 backdrop-blur animate-scale-in',
                style.ring,
              )}
            >
              <Icon className={cn('mt-0.5 h-5 w-5 shrink-0', style.iconColor)} />
              <div className="min-w-0 flex-1">
                <p className="text-sm font-semibold text-slate-900">{item.title}</p>
                {item.message ? (
                  <p className="mt-0.5 text-xs leading-relaxed text-slate-500">{item.message}</p>
                ) : null}
              </div>
              <button
                type="button"
                onClick={() => dismiss(item.id)}
                className="rounded-md p-1 text-slate-400 transition hover:bg-slate-100 hover:text-slate-600"
                aria-label="Dismiss notification"
              >
                <X className="h-4 w-4" />
              </button>
            </div>
          )
        })}
      </div>
    </ToastContext.Provider>
  )
}

export function useToast() {
  const context = useContext(ToastContext)
  if (!context) throw new Error('useToast must be used inside ToastProvider')
  return context
}
