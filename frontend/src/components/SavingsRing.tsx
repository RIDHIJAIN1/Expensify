export function SavingsRing({ percent }: { percent: number }) {
  const clamped = Math.max(0, Math.min(100, percent))
  const radius = 54
  const circumference = 2 * Math.PI * radius
  const offset = circumference - (clamped / 100) * circumference

  return (
    <div className="relative flex h-40 w-40 items-center justify-center">
      <svg viewBox="0 0 140 140" className="h-40 w-40 -rotate-90">
        <defs>
          <linearGradient id="savingsRingGradient" x1="0" y1="0" x2="1" y2="1">
            <stop offset="0%" stopColor="#6366f1" />
            <stop offset="100%" stopColor="#a855f7" />
          </linearGradient>
        </defs>
        <circle cx="70" cy="70" r={radius} fill="none" stroke="#eef2f7" strokeWidth="12" />
        <circle
          cx="70"
          cy="70"
          r={radius}
          fill="none"
          stroke="url(#savingsRingGradient)"
          strokeWidth="12"
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          style={{ transition: 'stroke-dashoffset 900ms cubic-bezier(0.22, 1, 0.36, 1)' }}
        />
      </svg>
      <div className="absolute flex flex-col items-center">
        <span className="font-display text-3xl font-extrabold tabular-nums text-slate-900">
          {Math.round(clamped)}%
        </span>
        <span className="text-[10px] font-bold uppercase tracking-widest text-slate-400">
          saved
        </span>
      </div>
    </div>
  )
}
