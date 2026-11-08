import { useId, useRef, useState } from 'react'

import { ApiError } from '../services/apiClient'
import { type Booking, confirmCash } from '../services/bookingService'
import { formatCurrency } from '../utils/format'

type Props = {
  maDon: string
  /** Tổng tiền do backend tính */
  tongTien: number
  onConfirmed: (booking: Booking) => void
  /** Backend trả 410: đơn đã hết hạn giữ hoặc đã hủy */
  onGone: () => void
  /** Lỗi 400 kèm tên trường (ví dụ chưa nhập điểm đón/trả) */
  onFieldError: (field: string, message: string) => void
  onCancel: () => void
}

/** Hộp xác nhận trả tiền mặt ngay trong trang; không dùng window.confirm. */
export default function CashConfirmDialog({ maDon, tongTien, onConfirmed, onGone, onFieldError, onCancel }: Props) {
  const [submitting, setSubmitting] = useState(false)
  const [message, setMessage] = useState('')
  // Chặn bấm liên tiếp trước khi kịp render lại nút vô hiệu
  const inFlight = useRef(false)
  const titleId = useId()

  async function confirm() {
    if (inFlight.current) return
    inFlight.current = true
    setSubmitting(true)
    setMessage('')
    try {
      onConfirmed(await confirmCash(maDon))
    } catch (error: unknown) {
      inFlight.current = false
      setSubmitting(false)
      if (error instanceof ApiError && error.status === 410) {
        onGone()
        return
      }
      const detail = error instanceof Error ? error.message : String(error)
      if (error instanceof ApiError && error.field) {
        onFieldError(error.field, detail)
        return
      }
      setMessage(detail)
    }
  }

  return (
    <div role="alertdialog" aria-labelledby={titleId} className="space-y-3 rounded-2xl border border-brand-200 bg-brand-50/70 p-4 shadow-2xs">
      <p id={titleId} className="text-xs font-bold uppercase tracking-wider text-brand-900">
        Xác nhận trả tiền mặt
      </p>
      <p className="text-xs text-slate-700">
        Bạn sẽ trả <strong className="font-bold text-amber-700">{formatCurrency(tongTien)}</strong> cho tài xế khi lên xe.
      </p>
      {message && (
        <p role="alert" className="text-xs font-semibold text-rose-700">
          {message}
        </p>
      )}
      <div className="flex flex-wrap items-center gap-2 pt-1">
        <button
          type="button"
          onClick={confirm}
          disabled={submitting}
          className="rounded-lg bg-brand-600 px-4 py-1.5 text-xs font-bold text-white shadow-2xs transition-all hover:bg-brand-700 active:scale-[0.98] disabled:opacity-50"
        >
          {submitting ? 'Đang xác nhận…' : 'Đồng ý'}
        </button>
        <button
          type="button"
          onClick={onCancel}
          disabled={submitting}
          className="rounded-lg border border-slate-300 bg-white px-3.5 py-1.5 text-xs font-semibold text-slate-700 hover:bg-slate-50 transition-colors disabled:opacity-50"
        >
          Quay lại
        </button>
      </div>
    </div>
  )
}
