const inr = new Intl.NumberFormat('en-IN', {
  style: 'currency',
  currency: 'INR',
  maximumFractionDigits: 0,
})

const inrPrecise = new Intl.NumberFormat('en-IN', {
  style: 'currency',
  currency: 'INR',
  minimumFractionDigits: 2,
  maximumFractionDigits: 2,
})

export function formatCurrency(value: number | string, precise = false): string {
  const n = typeof value === 'number' ? value : Number(value)
  return precise ? inrPrecise.format(n) : inr.format(n)
}

export function formatCompactCurrency(value: number | string): string {
  const n = typeof value === 'number' ? value : Number(value)
  if (Math.abs(n) >= 1_00_00_000) return `₹${(n / 1_00_00_000).toFixed(1)}Cr`
  if (Math.abs(n) >= 1_00_000) return `₹${(n / 1_00_000).toFixed(1)}L`
  if (Math.abs(n) >= 1_000) return `₹${(n / 1_000).toFixed(1)}K`
  return `₹${Math.round(n)}`
}

export function formatDate(value: string | Date): string {
  const date = typeof value === 'string' ? new Date(value) : value
  return date.toLocaleDateString('en-IN', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
    timeZone: 'UTC',
  })
}

export function formatDateInput(value: string | Date): string {
  const date = typeof value === 'string' ? new Date(value) : value
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

export function formatMonthLabel(value: string): string {
  const [year, month] = value.split('-').map(Number)
  const date = new Date(Date.UTC(year, month - 1, 1))
  return date.toLocaleDateString('en-IN', { month: 'short', year: '2-digit', timeZone: 'UTC' })
}

export function formatDateTimeSafe(value: string | Date): string {
  const date = typeof value === 'string' ? new Date(value) : value
  if (Number.isNaN(date.getTime())) return '—'
  return date.toLocaleString('en-IN', {
    day: '2-digit',
    month: 'short',
    hour: '2-digit',
    minute: '2-digit',
  })
}

export function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

export function relativeTime(value: string): string {
  const then = new Date(value).getTime()
  const seconds = Math.round((Date.now() - then) / 1000)
  if (seconds < 60) return 'just now'
  const minutes = Math.round(seconds / 60)
  if (minutes < 60) return `${minutes}m ago`
  const hours = Math.round(minutes / 60)
  if (hours < 24) return `${hours}h ago`
  const days = Math.round(hours / 24)
  if (days < 30) return `${days}d ago`
  return formatDate(value)
}

export function formatPercent(value: number): string {
  return `${value > 0 ? '+' : ''}${value.toFixed(1)}%`
}
