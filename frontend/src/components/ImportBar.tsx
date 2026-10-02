import { useRef } from 'react'
import { Download, Loader2, UploadCloud } from 'lucide-react'
import { cn } from '../lib/cn'

export function ImportBar({
  onFile,
  pending,
  active,
}: {
  onFile: (file: File) => void
  pending: boolean
  active: boolean
}) {
  const inputRef = useRef<HTMLInputElement>(null)

  return (
    <div
      onClick={() => inputRef.current?.click()}
      className={cn(
        'group flex cursor-pointer items-center gap-4 rounded-2xl border-2 border-dashed bg-white px-5 py-4 transition',
        active
          ? 'border-indigo-400 bg-indigo-50/70'
          : 'border-slate-200 hover:border-indigo-300 hover:bg-slate-50',
      )}
    >
      <span
        className={cn(
          'flex h-11 w-11 shrink-0 items-center justify-center rounded-xl transition',
          active
            ? 'bg-gradient-to-br from-indigo-600 to-violet-600 text-white'
            : 'bg-indigo-50 text-indigo-600 group-hover:scale-105',
        )}
      >
        {pending ? <Loader2 className="h-5 w-5 animate-spin" /> : <UploadCloud className="h-5 w-5" />}
      </span>
      <div className="min-w-0 flex-1">
        <p className="text-sm font-bold text-slate-800">
          {pending ? 'Importing statement…' : 'Drop your bank statement here — anywhere on this page'}
        </p>
        <p className="truncate text-xs text-slate-500">
          or click to browse · CSV · Date, Description, Amount, Type, Reference
        </p>
      </div>
      <a
        href="/sample_statement.csv"
        download="sample_statement.csv"
        onClick={(event) => event.stopPropagation()}
        className="hidden h-9 shrink-0 items-center gap-2 rounded-xl border border-slate-200 bg-white px-3.5 text-xs font-semibold text-slate-700 shadow-sm transition hover:bg-slate-50 sm:inline-flex"
      >
        <Download className="h-3.5 w-3.5" /> Sample CSV
      </a>
      <input
        ref={inputRef}
        type="file"
        accept=".csv,text/csv"
        className="hidden"
        onChange={(event) => {
          const file = event.target.files?.[0]
          if (file) onFile(file)
          event.target.value = ''
        }}
      />
    </div>
  )
}
