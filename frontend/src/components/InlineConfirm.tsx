import { useId, useRef, useState, type ReactNode } from 'react'

type Props = {
  title: string
  children: ReactNode
  confirmLabel?: string
  busyLabel?: string
  /** `danger` cho thao tác từ chối */
  tone?: 'brand' | 'danger'
  /** Lỗi do trang cha xử lý; hộp chỉ chặn bấm hai lần khi đang gửi */
  onConfirm: () => Promise<void>
  onCancel: () => void
}

const TONES = {
  brand: {
    box: 'border-brand-200 bg-brand-50/70',
    title: 'text-brand-900',
    button: 'bg-brand-600 hover:bg-brand-700',
  },
  danger: {
    box: 'border-rose-200 bg-rose-50/70',
    title: 'text-rose-900',
    button: 'bg-rose-600 hover:bg-rose-700',
  },
}

/** Hộp xác nhận ngay trong trang (không dùng window.confirm), cùng mẫu với trang Hoàn tiền. */
export default function InlineConfirm({
  title,
  children,
  confirmLabel = 'Đồng ý',
  busyLabel = 'Đang lưu…',
  tone = 'brand',
  onConfirm,
  onCancel,
}: Props) {
  const [submitting, setSubmitting] = useState(false)
  const inFlight = useRef(false)
  const titleId = useId()
  const styles = TONES[tone]

  async function confirm() {
    if (inFlight.current) return
    inFlight.current = true
    setSubmitting(true)
    try {
      await onConfirm()
    } finally {
      inFlight.current = false
      setSubmitting(false)
    }
  }

  return (
    <div role="alertdialog" aria-labelledby={titleId} className={`space-y-2.5 rounded-xl border p-3 text-xs ${styles.box}`}>
      <p id={titleId} className={`font-bold uppercase tracking-wider ${styles.title}`}>
        {title}
      </p>
      <div className="text-slate-700">{children}</div>
      <div className="flex flex-wrap gap-2">
        <button
          type="button"
          onClick={confirm}
          disabled={submitting}
          className={`flex-1 rounded-lg px-4 py-2 text-xs font-bold text-white shadow-2xs disabled:opacity-50 sm:flex-none ${styles.button}`}
        >
          {submitting ? busyLabel : confirmLabel}
        </button>
        <button
          type="button"
          onClick={onCancel}
          disabled={submitting}
          className="flex-1 rounded-lg border border-slate-300 bg-white px-3.5 py-2 text-xs font-semibold text-slate-700 hover:bg-slate-50 disabled:opacity-50 sm:flex-none"
        >
          Quay lại
        </button>
      </div>
    </div>
  )
}
