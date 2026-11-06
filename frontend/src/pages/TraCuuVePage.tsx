import { useState } from 'react'
import { Link } from 'react-router-dom'

import ExchangeModal from '../components/ExchangeModal'
import TicketList from '../components/TicketList'
import { lookupTicketsByPhone, type MyBooking, type Ticket } from '../services/bookingService'
import { formatCurrency, formatDate, formatTime, formatVehicleType } from '../utils/format'

export default function TraCuuVePage() {
  const [phone, setPhone] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [orders, setOrders] = useState<MyBooking[] | null>(null)

  const [exchangeTicket, setExchangeTicket] = useState<Ticket | null>(null)
  const [exchangeOrder, setExchangeOrder] = useState<MyBooking | null>(null)

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
    <section className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Tra cứu vé xe</h1>
        <p className="mt-1 text-sm text-slate-600">
          Nhập số điện thoại đã dùng khi đặt vé để tra cứu thông tin vé và thực hiện đổi vé.
        </p>
      </div>

      {/* Form tra cứu */}
      <form onSubmit={handleSearch} className="flex max-w-md gap-2">
        <input
          type="tel"
          placeholder="Nhập số điện thoại (ví dụ: 0900000001)"
          value={phone}
          onChange={(e) => setPhone(e.target.value)}
          className="flex-1 rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none"
        />
        <button
          type="submit"
          disabled={loading}
          className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-semibold text-white hover:bg-blue-700 disabled:opacity-50"
        >
          {loading ? 'Đang tra…' : 'Tra cứu'}
        </button>
      </form>

      {error && (
        <p role="alert" className="rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">
          {error}
        </p>
      )}

      {orders !== null && orders.length === 0 && (
        <div className="space-y-2">
          <p className="text-slate-600">Không tìm thấy vé nào được đặt với số điện thoại này.</p>
          <Link to="/tim-chuyen" className="font-medium text-blue-700 underline">
            Tìm chuyến & Đặt vé ngay
          </Link>
        </div>
      )}

      {orders && orders.length > 0 && (
        <ul aria-label="Đơn đặt vé tra cứu" className="space-y-4">
          {orders.map((order) => (
            <li
              key={order.ma_don}
              aria-label={`Đơn ${order.ma_don}`}
              className="space-y-3 rounded-lg border border-slate-200 bg-white p-4 shadow-xs"
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
              <TicketList
                tickets={order.ve}
                label={`Vé của đơn ${order.ma_don}`}
                onExchange={(ticket) => {
                  setExchangeTicket(ticket)
                  setExchangeOrder(order)
                }}
              />
              <p className="flex justify-between border-t border-slate-200 pt-2 font-semibold">
                <span>Tổng tiền</span>
                <span>{formatCurrency(order.tong_tien)}</span>
              </p>
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
