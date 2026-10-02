import { useId } from 'react'
import { Area, AreaChart, ResponsiveContainer } from 'recharts'

export function Sparkline({
  data,
  color = '#6366f1',
  height = 36,
}: {
  data: number[]
  color?: string
  height?: number
}) {
  const rawId = useId()
  const id = rawId.replace(/[^a-zA-Z0-9]/g, '')
  const series = data.map((value, index) => ({ index, value }))

  return (
    <div style={{ height }} className="w-full">
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={series} margin={{ top: 2, right: 0, left: 0, bottom: 0 }}>
          <defs>
            <linearGradient id={`spark-${id}`} x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor={color} stopOpacity={0.35} />
              <stop offset="100%" stopColor={color} stopOpacity={0} />
            </linearGradient>
          </defs>
          <Area
            type="monotone"
            dataKey="value"
            stroke={color}
            strokeWidth={2}
            fill={`url(#spark-${id})`}
            dot={false}
            isAnimationActive
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  )
}
