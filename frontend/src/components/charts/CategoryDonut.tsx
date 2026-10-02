import { useState } from 'react'
import { Cell, Pie, PieChart, ResponsiveContainer, Tooltip } from 'recharts'
import { formatCompactCurrency, formatCurrency } from '../../lib/format'
import { cn } from '../../lib/cn'
import { CategoryIcon } from '../CategoryIcon'

export interface DonutDatum {
  name: string
  total: number
  count: number
  color: string
}

function DonutTooltip({
  active,
  payload,
}: {
  active?: boolean
  payload?: { payload: DonutDatum & { share: number } }[]
}) {
  if (!active || !payload?.length) return null
  const item = payload[0].payload
  return (
    <div className="rounded-xl border border-slate-200 bg-white/95 px-3.5 py-2.5 shadow-pop">
      <p className="flex items-center gap-2 text-xs font-bold text-slate-900">
        <span className="h-2.5 w-2.5 rounded-full" style={{ backgroundColor: item.color }} />
        {item.name}
      </p>
      <p className="mt-1 text-xs text-slate-500">
        {formatCurrency(item.total, true)} · {item.share.toFixed(0)}% · {item.count} txns
      </p>
    </div>
  )
}

export function CategoryDonut({ data }: { data: DonutDatum[] }) {
  const [active, setActive] = useState<number | null>(null)
  const total = data.reduce((sum, item) => sum + item.total, 0)
  const enriched = data.map((item) => ({
    ...item,
    share: total ? (item.total / total) * 100 : 0,
  }))
  const focus = active !== null ? enriched[active] : null

  return (
    <div className="flex flex-col items-center gap-6 lg:flex-row">
      <div className="relative h-56 w-56 shrink-0">
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie
              data={enriched}
              dataKey="total"
              nameKey="name"
              innerRadius={68}
              outerRadius={96}
              paddingAngle={2.5}
              cornerRadius={6}
              strokeWidth={0}
              onMouseEnter={(_, index) => setActive(index)}
              onMouseLeave={() => setActive(null)}
            >
              {enriched.map((item, index) => (
                <Cell
                  key={item.name}
                  fill={item.color}
                  fillOpacity={active === null || active === index ? 1 : 0.22}
                  style={{ transition: 'fill-opacity 200ms ease' }}
                />
              ))}
            </Pie>
            <Tooltip content={<DonutTooltip />} />
          </PieChart>
        </ResponsiveContainer>

        <div className="pointer-events-none absolute inset-0 flex flex-col items-center justify-center px-10 text-center">
          {focus ? (
            <>
              <p className="truncate text-[10px] font-bold uppercase tracking-widest text-slate-400">
                {focus.name}
              </p>
              <p className="font-display text-lg font-extrabold tabular-nums text-slate-900">
                {formatCompactCurrency(focus.total)}
              </p>
              <p className="text-[11px] font-medium text-slate-400">
                {focus.share.toFixed(0)}% · {focus.count} txns
              </p>
            </>
          ) : (
            <>
              <p className="text-[10px] font-bold uppercase tracking-widest text-slate-400">
                Total spent
              </p>
              <p className="font-display text-xl font-extrabold tabular-nums text-slate-900">
                {formatCompactCurrency(total)}
              </p>
              <p className="text-[10px] text-slate-400">hover a category</p>
            </>
          )}
        </div>
      </div>

      <div className="no-scrollbar w-full flex-1 space-y-1 self-stretch overflow-y-auto lg:max-h-60">
        {enriched.slice(0, 8).map((item, index) => (
          <div
            key={item.name}
            onMouseEnter={() => setActive(index)}
            onMouseLeave={() => setActive(null)}
            className={cn(
              'group flex cursor-default items-center gap-3 rounded-xl px-3 py-2 transition',
              active === index ? 'bg-slate-50' : 'hover:bg-slate-50',
            )}
          >
            <CategoryIcon name={item.name} color={item.color} size="sm" />
            <div className="min-w-0 flex-1">
              <p className="truncate text-sm font-semibold text-slate-800">{item.name}</p>
              <div className="mt-1 h-1.5 w-full overflow-hidden rounded-full bg-slate-100">
                <div
                  className="h-full rounded-full transition-all duration-700"
                  style={{ width: `${Math.max(item.share, 2)}%`, backgroundColor: item.color }}
                />
              </div>
            </div>
            <div className="text-right">
              <p className="text-sm font-bold tabular-nums text-slate-900">
                {formatCompactCurrency(item.total)}
              </p>
              <p className="text-[11px] font-medium text-slate-400">{item.share.toFixed(0)}%</p>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
