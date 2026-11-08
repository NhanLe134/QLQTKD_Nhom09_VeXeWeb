import { useId, useState } from 'react'

import { type Booking, cancelBooking } from '../services/bookingService'

type Props = {
  maDon: string
  label?: string
  /** Gọi sau khi backend đã hủy đơn và đơn đã được xóa khỏi tab */
  onCancelled: (booking: Booking) => void
}

/** Nút hủy đơn kèm hộp xác nhận ngay trong trang (BR-BUS-33); không dùng window.confirm. */
export default function CancelBookingButton({ maDon, label = 'Hủy đặt vé', onCancelled }: Props) {
  const [confirming, setConfirming] = useState(false)
  const [submitting, setSubmitting] = useState(false)
  const [message, setMessage] = useState('')
  const titleId = useId()

  async function confirm() {
    setSubmitting(true)
    setMessage('')
    try {
      onCancelled(await cancelBooking(maDon))
    } catch (error: unknown) {
      setSubmitting(false)
      setMessage(error instanceof Error ? error.message : String(error))
    }
  }

  if (!confirming) {
    return (
      <button
        type="button"
        onClick={() => setConfirming(true)}
        className="rounded-lg border border-rose-200 bg-white px-3 py-1.5 text-xs font-semibold text-rose-700 hover:bg-rose-50 transition-colors"
      >
        {label}
      </button>
    )
  }

  return (
    <div role="alertdialog" aria-labelledby={titleId} className="space-y-2.5 rounded-xl border border-rose-200 bg-rose-50/80 p-3.5 text-xs">
      <p id={titleId} className="font-bold text-rose-900">
        Hủy đơn {maDon}?
      </p>
      <p className="text-rose-700">Các ghế đang giữ sẽ được nhả ngay cho người khác.</p>
      {message && (
        <p role="alert" className="text-xs font-semibold text-rose-800">
          {message}
        </p>
      )}
      <div className="flex flex-wrap items-center gap-2 pt-1">
        <button
          type="button"
          onClick={confirm}
          disabled={submitting}
          className="rounded-lg bg-rose-600 px-3 py-1.5 text-xs font-bold text-white shadow-2xs hover:bg-rose-700 disabled:opacity-50 transition-all"
        >
          {submitting ? 'Đang hủy…' : 'Đồng ý hủy'}
        </button>
        <button
          type="button"
          onClick={() => {
            setConfirming(false)
            setMessage('')
          }}
          disabled={submitting}
          className="rounded-lg border border-slate-300 bg-white px-3 py-1.5 text-xs font-semibold text-slate-700 hover:bg-slate-50 disabled:opacity-50 transition-colors"
        >
          Không hủy
        </button>
      </div>
    </div>
  )
}
