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
    <div role="alertdialog" aria-labelledby={titleId} className="space-y-3 rounded-lg border border-blue-200 bg-blue-50 p-4">
      <p id={titleId} className="font-semibold text-blue-900">
        Xác nhận trả tiền mặt
      </p>
      <p className="text-sm text-blue-900">Bạn sẽ trả {formatCurrency(tongTien)} cho tài xế khi lên xe.</p>
      {message && (
        <p role="alert" className="text-sm text-red-700">
          {message}
        </p>
      )}
      <div className="flex flex-col gap-2 sm:flex-row">
        <button
          type="button"
          onClick={confirm}
          disabled={submitting}
          className="rounded-md bg-blue-700 px-4 py-2 font-medium text-white hover:bg-blue-800 disabled:opacity-50"
        >
          {submitting ? 'Đang xác nhận…' : 'Đồng ý'}
        </button>
        <button
          type="button"
          onClick={onCancel}
          disabled={submitting}
          className="rounded-md border border-slate-300 bg-white px-4 py-2 font-medium text-slate-700 hover:bg-slate-50 disabled:opacity-50"
        >
          Quay lại
        </button>
      </div>
    </div>
  )
}
