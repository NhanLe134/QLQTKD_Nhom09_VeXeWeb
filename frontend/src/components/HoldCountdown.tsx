import { formatCountdown } from '../utils/format'

/** BR-BUS-17: còn 2 phút thì nhắc khách. */
export const HOLD_WARNING_MS = 2 * 60 * 1000

type Props = {
  /** Số ms còn lại (useCountdown); null là không còn ghế đang giữ */
  remainingMs: number | null
}

export default function HoldCountdown({ remainingMs }: Props) {
  if (remainingMs === null || remainingMs <= 0) {
    return (
      <p role="alert" className="rounded-md bg-red-50 px-3 py-2 font-medium text-red-700">
        Hết thời gian giữ chỗ
      </p>
    )
  }

  const warning = remainingMs <= HOLD_WARNING_MS
  return (
    <div className="space-y-2">
      <p className="text-slate-700">
        Thời gian giữ chỗ còn lại:{' '}
        <span
          role="timer"
          aria-label="Thời gian giữ chỗ còn lại"
          className={`font-mono text-lg font-semibold ${warning ? 'text-red-600' : 'text-blue-700'}`}
        >
          {formatCountdown(remainingMs)}
        </span>
      </p>
      {warning && (
        <p role="alert" className="rounded-md bg-amber-50 px-3 py-2 text-sm text-amber-800">
          Sắp hết thời gian giữ chỗ, vui lòng hoàn tất đặt vé.
        </p>
      )}
    </div>
  )
}
