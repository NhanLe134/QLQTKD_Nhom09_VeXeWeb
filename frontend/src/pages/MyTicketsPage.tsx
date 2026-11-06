import { useCallback, useEffect, useState } from 'react'
import { Link } from 'react-router-dom'

import ExchangeModal from '../components/ExchangeModal'
import TicketList from '../components/TicketList'
import { getMyTickets, lookupTicketsByPhone, type MyBooking, type Ticket } from '../services/bookingService'
import { formatCurrency, formatDate, formatTime, formatVehicleType } from '../utils/format'

type State =
  | { state: 'loading' }
  | { state: 'loaded'; data: MyBooking[] }
  | { state: 'error'; message: string }

/** "Vé của tôi" (BR-BUS-36): đơn đã xác nhận của khách đang đăng nhập, gom vé theo mã đơn. */
export default function MyTicketsPage() {
  const [result, setResult] = useState<State>({ state: 'loading' })
  const [phoneSearch, setPhoneSearch] = useState('')
  const [searching, setSearching] = useState(false)

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

  const handlePhoneSearch = async (e: React.FormEvent) => {
    e.preventDefault()
    const cleanPhone = phoneSearch.trim()
    if (!cleanPhone) {
      setResult({ state: 'loading' })
      reloadTickets()
      return
    }
    setSearching(true)
    try {
      const data = await lookupTicketsByPhone(cleanPhone)
      setResult({ state: 'loaded', data })
    } catch (err) {
      setResult({ state: 'error', message: err instanceof Error ? err.message : 'Tra cứu thất bại.' })
    } finally {
      setSearching(false)
    }
  }

  return (
    <section className="space-y-4">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <h1 className="text-2xl font-bold">Vé của tôi</h1>
        <form onSubmit={handlePhoneSearch} className="flex gap-2">
          <input
            type="tel"
            placeholder="Tra cứu theo SĐT khác…"
            value={phoneSearch}
            onChange={(e) => setPhoneSearch(e.target.value)}
            className="rounded border border-slate-300 px-3 py-1.5 text-xs focus:border-blue-500 focus:outline-none"
          />
          <button
            type="submit"
            disabled={searching}
            className="rounded bg-slate-800 px-3 py-1.5 text-xs font-semibold text-white hover:bg-slate-700 disabled:opacity-50"
          >
            {searching ? 'Đang tìm…' : 'Tra cứu'}
          </button>
        </form>
      </div>

      {result.state === 'loading' && (
        <p role="status" className="text-slate-600">
          Đang tải vé…
        </p>
      )}
      {result.state === 'error' && (
        <p role="alert" className="rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">
          {result.message}
        </p>
      )}
      {result.state === 'loaded' && result.data.length === 0 && (
        <div className="space-y-2">
          <p className="text-slate-600">Bạn chưa có vé nào.</p>
          <Link to="/tim-chuyen" className="font-medium text-blue-700 underline">
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
