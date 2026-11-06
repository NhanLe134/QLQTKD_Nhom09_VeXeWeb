import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'

import TicketList from '../components/TicketList'
import { getMyTickets, type MyBooking } from '../services/bookingService'
import { formatCurrency, formatDate, formatTime, formatVehicleType } from '../utils/format'

type State =
  | { state: 'loading' }
  | { state: 'loaded'; data: MyBooking[] }
  | { state: 'error'; message: string }

/** "Vé của tôi" (BR-BUS-36): đơn đã xác nhận của khách đang đăng nhập, gom vé theo mã đơn. */
export default function MyTicketsPage() {
  const [result, setResult] = useState<State>({ state: 'loading' })

  useEffect(() => {
    let cancelled = false
    getMyTickets()
      .then((data) => {
        if (!cancelled) setResult({ state: 'loaded', data })
      })
      .catch((error: unknown) => {
        if (!cancelled) setResult({ state: 'error', message: error instanceof Error ? error.message : String(error) })
      })
    return () => {
      cancelled = true
    }
  }, [])

  return (
    <section className="space-y-4">
      <h1 className="text-2xl font-bold text-brand-800">Vé của tôi</h1>
      {result.state === 'loading' && (
        <p role="status" className="text-slate-600">
          Đang tải vé…
        </p>
      )}
      {result.state === 'error' && (
        <p role="alert" className="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700">
          {result.message}
        </p>
      )}
      {result.state === 'loaded' && result.data.length === 0 && (
        <div className="space-y-2">
          <p className="text-slate-600">Bạn chưa có vé nào.</p>
          <Link to="/tim-chuyen" className="font-medium text-brand-700 underline">
            Tìm chuyến
          </Link>
        </div>
      )}
      {result.state === 'loaded' && result.data.length > 0 && (
        <ul aria-label="Đơn đặt vé" className="space-y-4">
          {result.data.map((order) => (
            <li
              key={order.ma_don}
              aria-label={`Đơn ${order.ma_don}`}
              className="space-y-3 rounded-xl border border-brand-100 bg-white shadow-sm p-4"
            >
              <div className="space-y-1">
                <p className="text-slate-600">
                  Mã đơn: <span className="font-semibold text-slate-900">{order.ma_don}</span>
                </p>
                <p className="text-lg font-semibold">{order.chuyen.ten_tuyen}</p>
                <p className="text-slate-700">
                  {formatTime(order.chuyen.gio_di)} ngày {formatDate(order.chuyen.ngay_khoi_hanh)}
                </p>
                <p className="text-sm text-slate-600">
                  {formatVehicleType(order.chuyen.ten_loai_xe, order.chuyen.so_cho)}
                </p>
              </div>
              <TicketList tickets={order.ve} label={`Vé của đơn ${order.ma_don}`} />
              <p className="flex justify-between border-t border-slate-200 pt-2 font-semibold">
                <span>Tổng tiền</span>
                <span>{formatCurrency(order.tong_tien)}</span>
              </p>
            </li>
          ))}
        </ul>
      )}
    </section>
  )
}
