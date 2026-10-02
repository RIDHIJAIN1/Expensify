import { useCountUp } from '../hooks/useCountUp'
import { formatCurrency } from '../lib/format'

export function AnimatedValue({
  value,
  format = formatCurrency,
}: {
  value: number
  format?: (n: number) => string
}) {
  const animated = useCountUp(value)
  return <>{format(animated)}</>
}
