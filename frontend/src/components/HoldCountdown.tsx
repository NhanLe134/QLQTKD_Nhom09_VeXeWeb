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
      <p role="alert" className="rounded-xl bg-rose-50 px-3.5 py-2 text-xs font-bold text-rose-700 ring-1 ring-rose-200/70">
        Hết thời gian giữ chỗ
      </p>
    )
  }

  const warning = remainingMs <= HOLD_WARNING_MS
  return (
    <div className="space-y-2">
      <div className={`flex items-center justify-between gap-2 rounded-xl border px-3.5 py-2 text-xs shadow-2xs transition-colors ${
        warning ? 'border-amber-300 bg-amber-50/70' : 'border-slate-200/90 bg-white'
      }`}>
        <span className="font-medium text-slate-700">
          Thời gian giữ chỗ còn lại:{' '}
        </span>
        <span
          role="timer"
          aria-label="Thời gian giữ chỗ còn lại"
          className={`font-mono text-sm font-black ${warning ? 'text-rose-600 animate-pulse' : 'text-brand-700'}`}
        >
          {formatCountdown(remainingMs)}
        </span>
      </div>
      {warning && (
        <p role="alert" className="rounded-lg bg-amber-50 px-3 py-1.5 text-xs font-semibold text-amber-900 ring-1 ring-amber-200/60">
          Sắp hết thời gian giữ chỗ, vui lòng hoàn tất đặt vé.
        </p>
      )}
    </div>
  )
}
