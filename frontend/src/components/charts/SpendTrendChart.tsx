import { Area, AreaChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import type { MonthlyTotal } from '../../lib/types'
import { formatCompactCurrency, formatCurrency, formatMonthLabel } from '../../lib/format'

type Point = { label: string; debit: number; credit: number }

function TrendTooltip({ active, payload }: { active?: boolean; payload?: { payload: Point }[] }) {
  if (!active || !payload?.length) return null
  const point = payload[0].payload
  return (
    <div className="rounded-xl border border-slate-200 bg-white/95 px-3.5 py-3 shadow-pop backdrop-blur">
      <p className="mb-1.5 text-xs font-bold text-slate-900">{point.label}</p>
      <div className="space-y-1 text-xs">
        <p className="flex items-center justify-between gap-6">
          <span className="flex items-center gap-1.5 text-slate-500">
            <span className="h-2 w-2 rounded-full bg-indigo-500" /> Spent
          </span>
          <span className="font-bold text-slate-900">{formatCurrency(point.debit, true)}</span>
        </p>
        <p className="flex items-center justify-between gap-6">
          <span className="flex items-center gap-1.5 text-slate-500">
            <span className="h-2 w-2 rounded-full bg-emerald-500" /> Received
          </span>
          <span className="font-bold text-slate-900">{formatCurrency(point.credit, true)}</span>
        </p>
      </div>
    </div>
  )
}

export function SpendTrendChart({ data, height = 300 }: { data: MonthlyTotal[]; height?: number }) {
  const series: Point[] = data.map((d) => ({
    label: formatMonthLabel(d.month),
    debit: Number(d.debit),
    credit: Number(d.credit),
  }))

  return (
    <div style={{ height }} className="w-full">
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={series} margin={{ top: 10, right: 8, left: 0, bottom: 0 }}>
          <defs>
            <linearGradient id="debitGradient" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#6366f1" stopOpacity={0.32} />
              <stop offset="100%" stopColor="#6366f1" stopOpacity={0.02} />
            </linearGradient>
            <linearGradient id="creditGradient" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#10b981" stopOpacity={0.28} />
              <stop offset="100%" stopColor="#10b981" stopOpacity={0.02} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 6" stroke="#e2e8f0" vertical={false} />
          <XAxis
            dataKey="label"
            tick={{ fontSize: 11, fill: '#94a3b8', fontWeight: 600 }}
            tickLine={false}
            axisLine={false}
            minTickGap={24}
          />
          <YAxis
            tickFormatter={(value: number) => formatCompactCurrency(value)}
            tick={{ fontSize: 11, fill: '#94a3b8', fontWeight: 600 }}
            tickLine={false}
            axisLine={false}
            width={56}
          />
          <Tooltip content={<TrendTooltip />} cursor={{ stroke: '#c7d2fe', strokeWidth: 1.5 }} />
          <Area
            type="monotone"
            dataKey="credit"
            stroke="#10b981"
            strokeWidth={2}
            fill="url(#creditGradient)"
            dot={false}
            activeDot={{ r: 4, strokeWidth: 2, stroke: '#fff' }}
          />
          <Area
            type="monotone"
            dataKey="debit"
            stroke="#6366f1"
            strokeWidth={2.4}
            fill="url(#debitGradient)"
            dot={false}
            activeDot={{ r: 4, strokeWidth: 2, stroke: '#fff' }}
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  )
}
