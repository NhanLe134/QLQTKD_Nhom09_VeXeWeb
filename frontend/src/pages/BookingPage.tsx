import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'

import BookingFailed, { type FailureReason } from '../components/BookingFailed'
import CancelBookingButton from '../components/CancelBookingButton'
import HoldCountdown from '../components/HoldCountdown'
import { useCountdown } from '../hooks/useCountdown'
import { type Booking, getBooking } from '../services/bookingService'
import { clearStoredBookingFor } from '../utils/bookingStorage'
import { formatCurrency, formatDate, formatTime, formatVehicleType } from '../utils/format'

type BookingState =
  | { state: 'loading' }
  | { state: 'loaded'; data: Booking; clockOffsetMs: number }
  | { state: 'error'; message: string }

export default function BookingPage() {
  const { maDon = '' } = useParams()
  const [booking, setBooking] = useState<BookingState>({ state: 'loading' })

  useEffect(() => {
    let cancelled = false
    getBooking(maDon)
      .then((data) => {
        if (cancelled) return
        // Độ lệch giữa giờ server và máy khách, để đếm ngược đúng hạn giữ của server
        const clockOffsetMs = Date.parse(data.thoi_diem_hien_tai) - Date.now()
        setBooking({ state: 'loaded', data, clockOffsetMs })
      })
      .catch((error: unknown) => {
        if (!cancelled) setBooking({ state: 'error', message: error instanceof Error ? error.message : String(error) })
      })
    return () => {
      cancelled = true
    }
  }, [maDon])

  if (booking.state !== 'loaded') {
    return (
      <section className="space-y-4">
        <h1 className="text-2xl font-bold">Đặt vé</h1>
        {booking.state === 'loading' ? (
          <p role="status" className="text-slate-600">
            Đang tải đơn…
          </p>
        ) : (
          <p role="alert" className="rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">
            {booking.message}
          </p>
        )}
      </section>
    )
  }

  return <BookingDetail data={booking.data} clockOffsetMs={booking.clockOffsetMs} />
}

// Tách riêng để useCountdown bắt đầu đếm đúng lúc đã có dữ liệu đơn
function BookingDetail({ data, clockOffsetMs }: { data: Booking; clockOffsetMs: number }) {
  const [cancelled, setCancelled] = useState(false)
  const dangGiu = data.trang_thai_don === 'DANG_GIU'
  const remainingMs = useCountdown(dangGiu ? data.han_giu_cho : null, clockOffsetMs)
  // Hết giờ trên đồng hồ thì coi như hết giữ chỗ ngay, không chờ tải lại đơn
  const holding = remainingMs !== null && remainingMs > 0
  const failure = failureReason(data, cancelled, dangGiu && !holding)
  const { chuyen } = data
  const heldTickets = data.ve.filter((ve) => ve.trang_thai_ve !== 'DA_HUY')

  useEffect(() => {
    if (failure) clearStoredBookingFor(data.ma_don)
  }, [failure, data.ma_don])

  if (failure) {
    return <BookingFailed reason={failure} maDon={data.ma_don} chuyenXeId={chuyen.chuyen_xe_id} />
  }

  return (
    <section className="space-y-4">
      <h1 className="text-2xl font-bold">Đặt vé</h1>
      <p className="text-slate-600">
        Mã đơn: <span className="font-semibold text-slate-900">{data.ma_don}</span>
      </p>

      {dangGiu ? (
        <HoldCountdown remainingMs={remainingMs} />
      ) : (
        <p role="status" className="rounded-md bg-green-50 px-3 py-2 font-medium text-green-700">
          Đơn đã được xác nhận.
        </p>
      )}

      <div className="space-y-1 rounded-lg border border-slate-200 bg-white p-4">
        <p className="text-lg font-semibold">{chuyen.ten_tuyen}</p>
        <p className="text-slate-700">
          {formatTime(chuyen.gio_di)} ngày {formatDate(chuyen.ngay_khoi_hanh)}
        </p>
        <p className="text-sm text-slate-600">{formatVehicleType(chuyen.ten_loai_xe, chuyen.so_cho)}</p>
      </div>

      <div className="space-y-2 rounded-lg border border-slate-200 bg-white p-4">
        <h2 className="font-semibold">Ghế đã giữ</h2>
        <ul aria-label="Ghế đã giữ" className="divide-y divide-slate-100">
          {heldTickets.map((ve) => (
            <li key={ve.ve_id} className="flex justify-between py-1">
              <span>Ghế {ve.so_ghe}</span>
              <span>{formatCurrency(ve.gia_ve)}</span>
            </li>
          ))}
        </ul>
        <p className="flex justify-between border-t border-slate-200 pt-2 font-semibold">
          <span>Tổng tiền</span>
          <span data-testid="tong-tien">{formatCurrency(data.tong_tien)}</span>
        </p>
      </div>

      {holding && (
        <>
          <div className="space-y-1 rounded-lg border border-dashed border-slate-300 p-4">
            <h2 className="font-semibold">Thông tin hành khách</h2>
            {/* Task #9: nhập hành khách từng ghế, điểm đón/trả */}
            <p className="text-sm text-slate-600">Đang xây dựng.</p>
          </div>
          <CancelBookingButton maDon={data.ma_don} onCancelled={() => setCancelled(true)} />
        </>
      )}
    </section>
  )
}

/** Lý do biết ngay trên trang (tự hủy, hết giờ) ưu tiên hơn trạng thái tải từ backend. */
function failureReason(data: Booking, cancelled: boolean, timedOut: boolean): FailureReason | null {
  if (cancelled) return 'TU_HUY'
  if (timedOut) return 'HET_GIO'
  if (data.trang_thai_don === 'HET_HAN' || data.trang_thai_don === 'DA_HUY') return data.trang_thai_don
  return null
}
