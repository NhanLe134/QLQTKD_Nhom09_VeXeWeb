import { useCallback, useEffect, useState } from 'react'
import { Link } from 'react-router-dom'

import ExchangeModal from '../components/ExchangeModal'
import TicketList from '../components/TicketList'
import { getMyTickets, type MyBooking, type Ticket } from '../services/bookingService'
import { formatCurrency, formatDate, formatTime, formatVehicleType } from '../utils/format'

type State =
  | { state: 'loading' }
  | { state: 'loaded'; data: MyBooking[] }
  | { state: 'error'; message: string }

/** "Vé của tôi" (BR-BUS-36): đơn đã xác nhận của khách đang đăng nhập, gom vé theo mã đơn. */
export default function MyTicketsPage() {
  const [result, setResult] = useState<State>({ state: 'loading' })

  const [exchangeTicket, setExchangeTicket] = useState<Ticket | null>(null)
  const [exchangeOrder, setExchangeOrder] = useState<MyBooking | null>(null)

  const reloadTickets = useCallback(() => {
    getMyTickets()
      .then((data) => setResult({ state: 'loaded', data }))
      .catch((error: unknown) => {
        setResult({ state: 'error', message: error instanceof Error ? error.message : String(error) })
      })
  }, [])

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
      <div>
        <h1 className="text-xl sm:text-2xl font-bold tracking-tight text-slate-900">Vé của tôi</h1>
        <p className="mt-0.5 text-xs text-slate-500">Các vé đã xác nhận của tài khoản.</p>
      </div>

      {result.state === 'loading' && (
        <div className="flex items-center justify-center py-8">
          <p role="status" className="inline-flex items-center gap-2 rounded-lg bg-white px-4 py-2 text-xs font-medium text-slate-600 shadow-2xs border border-slate-200/80">
            <span className="h-3.5 w-3.5 animate-spin rounded-full border-2 border-brand-600 border-t-transparent" />
            Đang tải vé…
          </p>
        </div>
      )}

      {result.state === 'error' && (
        <p role="alert" className="rounded-xl bg-rose-50 p-3 text-xs font-semibold text-rose-700 ring-1 ring-rose-200/70">
          {result.message}
        </p>
      )}

      {result.state === 'loaded' && result.data.length === 0 && (
        <div className="space-y-2 rounded-2xl border border-slate-200/90 bg-white p-5 text-center shadow-2xs">
          <p className="text-xs sm:text-sm font-medium text-slate-600">Bạn chưa có vé nào.</p>
          <Link to="/tim-chuyen" className="inline-block text-xs font-bold text-brand-700 underline hover:no-underline">
            Tìm chuyến
          </Link>
        </div>
      )}

      {result.state === 'loaded' && result.data.length > 0 && (
        <ul aria-label="Đơn đặt vé" className="space-y-3">
          {result.data.map((order) => (
            <li
              key={order.ma_don}
              aria-label={`Đơn ${order.ma_don}`}
              className="space-y-3 rounded-xl border border-slate-200/90 bg-white p-4 shadow-2xs"
            >
              {/* Header đơn hàng */}
              <div className="flex flex-col gap-1 border-b border-slate-100 pb-2.5 sm:flex-row sm:items-center sm:justify-between">
                <div>
                  <div className="flex items-center gap-2">
                    <p className="text-sm font-bold text-slate-900">{order.chuyen.ten_tuyen}</p>
                    <span className="rounded bg-slate-100 px-1.5 py-0.5 text-[10px] font-semibold text-slate-600">
                      {formatVehicleType(order.chuyen.ten_loai_xe, order.chuyen.so_cho)}
                    </span>
                  </div>
                  <p className="text-xs text-slate-500 mt-0.5">
                    {formatTime(order.chuyen.gio_di)} ngày {formatDate(order.chuyen.ngay_khoi_hanh)}
                  </p>
                </div>
                <div>
                  <span className="inline-block rounded-md bg-slate-100 px-2 py-0.5 text-[11px] font-semibold text-slate-600">
                    Mã đơn: <strong className="font-mono text-slate-900">{order.ma_don}</strong>
                  </span>
                </div>
              </div>

              {/* Danh sách vé */}
              <TicketList
                tickets={order.ve}
                label={`Vé của đơn ${order.ma_don}`}
                onExchange={(ticket) => {
                  setExchangeTicket(ticket)
                  setExchangeOrder(order)
                }}
              />

              {/* Tổng tiền */}
              <div className="flex items-center justify-between border-t border-slate-100 pt-2 text-xs font-bold text-slate-800">
                <span>Tổng tiền</span>
                <span className="text-sm sm:text-base font-extrabold text-amber-600">{formatCurrency(order.tong_tien)}</span>
              </div>
            </li>
          ))}
        </ul>
      )}

      {/* Modal Đổi vé */}
      {exchangeTicket && (
        <ExchangeModal
          ticket={exchangeTicket}
          currentOrder={exchangeOrder}
          onClose={() => {
            setExchangeTicket(null)
            setExchangeOrder(null)
          }}
          onSuccess={reloadTickets}
        />
      )}
    </section>
  )
}
