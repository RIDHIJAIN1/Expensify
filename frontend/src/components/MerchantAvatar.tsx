import { cn } from '../lib/cn'

const GRADIENTS = [
  'from-indigo-500 to-violet-600',
  'from-emerald-500 to-teal-600',
  'from-rose-500 to-orange-500',
  'from-sky-500 to-indigo-600',
  'from-fuchsia-500 to-pink-600',
  'from-amber-500 to-rose-500',
]

function hash(text: string) {
  let value = 0
  for (let i = 0; i < text.length; i++) value = (value * 31 + text.charCodeAt(i)) >>> 0
  return value
}

export function MerchantAvatar({ name, size = 'md' }: { name: string; size?: 'sm' | 'md' }) {
  const initials = name
    .split(/\s+/)
    .map((word) => word[0])
    .filter(Boolean)
    .slice(0, 2)
    .join('')
    .toUpperCase()

  return (
    <span
      className={cn(
        'flex shrink-0 items-center justify-center rounded-xl bg-gradient-to-br font-bold text-white shadow-sm',
        size === 'sm' ? 'h-8 w-8 text-[11px]' : 'h-10 w-10 text-xs',
        GRADIENTS[hash(name) % GRADIENTS.length],
      )}
    >
      {initials}
    </span>
  )
}
