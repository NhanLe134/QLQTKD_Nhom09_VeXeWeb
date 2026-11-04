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
        className="rounded-lg border border-red-300 px-4 py-2 font-medium text-red-700 hover:bg-red-50"
      >
        {label}
      </button>
    )
  }

  return (
    <div role="alertdialog" aria-labelledby={titleId} className="space-y-3 rounded-lg border border-red-200 bg-red-50 p-4">
      <p id={titleId} className="font-semibold text-red-800">
        Hủy đơn {maDon}?
      </p>
      <p className="text-sm text-red-700">Các ghế đang giữ sẽ được nhả ngay cho người khác.</p>
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
          className="rounded-lg bg-red-700 px-4 py-2 font-medium text-white hover:bg-red-800 disabled:opacity-50"
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
          className="rounded-lg border border-slate-300 bg-white px-4 py-2 font-medium text-slate-700 hover:bg-slate-50 disabled:opacity-50"
        >
          Không hủy
        </button>
      </div>
    </div>
  )
}
