import {
  Circle,
  Clapperboard,
  HeartPulse,
  Plane,
  ShoppingBag,
  Tag,
  TrendingUp,
  UtensilsCrossed,
  Zap,
  type LucideIcon,
} from 'lucide-react'
import { cn } from '../lib/cn'

const ICONS: Record<string, LucideIcon> = {
  Food: UtensilsCrossed,
  Travel: Plane,
  Utilities: Zap,
  Shopping: ShoppingBag,
  Entertainment: Clapperboard,
  Healthcare: HeartPulse,
  Income: TrendingUp,
  Other: Circle,
}

export function CategoryIcon({
  name,
  color,
  size = 'md',
}: {
  name: string
  color?: string | null
  size?: 'sm' | 'md' | 'lg'
}) {
  const Icon = ICONS[name] ?? Tag
  const tint = color || '#64748b'
  const box = size === 'sm' ? 'h-8 w-8 rounded-lg' : size === 'lg' ? 'h-12 w-12 rounded-2xl' : 'h-10 w-10 rounded-xl'
  const px = size === 'sm' ? 15 : size === 'lg' ? 22 : 18
  return (
    <span
      className={cn('flex shrink-0 items-center justify-center', box)}
      style={{ backgroundColor: `${tint}1a`, color: tint }}
    >
      <Icon size={px} strokeWidth={2.1} />
    </span>
  )
}
