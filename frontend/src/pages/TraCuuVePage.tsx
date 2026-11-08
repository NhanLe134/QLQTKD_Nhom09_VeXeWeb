import { useState } from 'react'
import { Link, Navigate } from 'react-router-dom'

import ExchangeModal from '../components/ExchangeModal'
import { SearchIcon } from '../components/icons'
import TicketList from '../components/TicketList'
import { useAuth } from '../hooks/useAuth'
import { lookupTicketsByPhone, type MyBooking, type Ticket } from '../services/bookingService'
import { formatCurrency, formatDate, formatTime, formatVehicleType } from '../utils/format'

export default function TraCuuVePage() {
  const { user } = useAuth()
  const [phone, setPhone] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [orders, setOrders] = useState<MyBooking[] | null>(null)

  const [exchangeTicket, setExchangeTicket] = useState<Ticket | null>(null)
  const [exchangeOrder, setExchangeOrder] = useState<MyBooking | null>(null)

  if (user?.vai_tro === 'KHACH') {
    return <Navigate to="/ve-cua-toi" replace />
  }

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault()
    const cleanPhone = phone.trim()
    if (!cleanPhone) return
    if (!/^0\d{9}$/.test(cleanPhone)) {
      setError('Số điện thoại phải gồm 10 chữ số và bắt đầu bằng số 0.')
      return
    }

    setLoading(true)
    setError(null)
    try {
      const data = await lookupTicketsByPhone(cleanPhone)
      setOrders(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Tra cứu vé thất bại.')
    } finally {
      setLoading(false)
    }
  }

  const reloadTickets = () => {
    if (phone.trim()) {
      lookupTicketsByPhone(phone.trim())
        .then(setOrders)
        .catch(() => {})
    }
  }

  return (
    <section className="space-y-4">
      <div>
        <h1 className="text-xl sm:text-2xl font-bold tracking-tight text-slate-900">Tra cứu vé</h1>
        <p className="mt-0.5 text-xs text-slate-500">
          Nhập số điện thoại đã dùng khi đặt vé để tra cứu thông tin vé.
        </p>
      </div>

      {/* Form tra cứu nhỏ gọn */}
      <form onSubmit={handleSearch} className="flex max-w-md items-center gap-2">
        <div className="relative flex-1">
          <input
            type="tel"
            placeholder="Nhập số điện thoại"
            value={phone}
            onChange={(e) => setPhone(e.target.value)}
            className="w-full rounded-lg border border-slate-300 bg-white px-3 py-1.5 text-xs sm:text-sm font-medium text-slate-900 outline-none transition-all focus:border-brand-500 focus:ring-2 focus:ring-brand-100"
          />
        </div>
        <button
          type="submit"
          disabled={loading}
          className="inline-flex h-[34px] items-center justify-center gap-1.5 rounded-lg bg-brand-600 px-4 text-xs font-bold text-white shadow-2xs transition-all hover:bg-brand-700 active:scale-[0.98] disabled:opacity-50"
        >
          <SearchIcon className="h-3.5 w-3.5" />
          <span>{loading ? 'Đang tra…' : 'Tra cứu'}</span>
        </button>
      </form>

      {error && (
        <p role="alert" className="rounded-xl bg-rose-50 p-3 text-xs font-semibold text-rose-700 ring-1 ring-rose-200/70">
          {error}
        </p>
      )}

      {orders !== null && orders.length === 0 && (
        <div className="space-y-2 rounded-2xl border border-slate-200/90 bg-white p-5 text-center shadow-2xs">
          <p className="text-xs sm:text-sm font-medium text-slate-600">Không tìm thấy vé nào được đặt với số điện thoại này.</p>
          <Link to="/tim-chuyen" className="inline-block text-xs font-bold text-brand-700 underline hover:no-underline">
            Tìm chuyến &amp; Đặt vé ngay
          </Link>
        </div>
      )}

      {orders && orders.length > 0 && (
        <ul aria-label="Đơn đặt vé tra cứu" className="space-y-3">
          {orders.map((order) => (
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
