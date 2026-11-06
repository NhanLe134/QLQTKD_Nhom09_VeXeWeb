import { useEffect, useState } from 'react'
import { exchangeTicket, type MyBooking, type Ticket } from '../services/bookingService'
import {
  getLocations,
  getTripSeats,
  searchTrips,
  type Locations,
  type Seat,
  type Trip,
} from '../services/tripService'
import { formatCurrency, formatDate, formatTime } from '../utils/format'

type Props = {
  ticket: Ticket | null
  currentOrder?: MyBooking | null
  onClose: () => void
  onSuccess: () => void
}

export default function ExchangeModal({ ticket, currentOrder, onClose, onSuccess }: Props) {
  const [locations, setLocations] = useState<Locations>({ diem_di: [], diem_den: [] })
  const [diemDi, setDiemDi] = useState(currentOrder?.chuyen.diem_di ?? '')
  const [diemDen, setDiemDen] = useState(currentOrder?.chuyen.diem_den ?? '')
  const [ngay, setNgay] = useState(currentOrder?.chuyen.ngay_khoi_hanh ?? '')

  const [trips, setTrips] = useState<Trip[]>([])
  const [searchingTrips, setSearchingTrips] = useState(false)
  const [searchError, setSearchError] = useState<string | null>(null)

  const [selectedTrip, setSelectedTrip] = useState<Trip | null>(null)
  const [seats, setSeats] = useState<Seat[]>([])
  const [loadingSeats, setLoadingSeats] = useState(false)
  const [selectedSeat, setSelectedSeat] = useState<Seat | null>(null)

  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [successMsg, setSuccessMsg] = useState<string | null>(null)

  useEffect(() => {
    getLocations()
      .then((locs) => {
        setLocations(locs)
        if (!diemDi && locs.diem_di.length > 0) setDiemDi(locs.diem_di[0])
        if (!diemDen && locs.diem_den.length > 0) setDiemDen(locs.diem_den[0])
      })
      .catch(() => {})
  }, [diemDi, diemDen])

  const handleSearchTrips = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!diemDi || !diemDen || !ngay) return
    setSearchingTrips(true)
    setSearchError(null)
    setSelectedTrip(null)
    setSelectedSeat(null)
    setSeats([])
    try {
      const res = await searchTrips({ diemDi, diemDen, ngay })
      const allTrips = [...res.chuyen, ...res.goi_y]
      setTrips(allTrips)
      if (allTrips.length === 0) {
        setSearchError('Không tìm thấy chuyến xe nào phù hợp.')
      }
    } catch (err) {
      setSearchError(err instanceof Error ? err.message : 'Lỗi khi tìm chuyến xe.')
    } finally {
      setSearchingTrips(false)
    }
  }

  const handleSelectTrip = async (trip: Trip) => {
    setSelectedTrip(trip)
    setSelectedSeat(null)
    setLoadingSeats(true)
    try {
      const seatMap = await getTripSeats(trip.chuyen_xe_id)
      setSeats(seatMap.ghe.filter((g) => g.trang_thai === 'TRONG'))
    } catch {
      setSeats([])
    } finally {
      setLoadingSeats(false)
    }
  }

  if (!ticket) return null

  const isPriceHigher = selectedTrip ? selectedTrip.gia_ve > ticket.gia_ve : false

  const handleConfirmExchange = async () => {
    if (!selectedTrip || !selectedSeat) return
    if (isPriceHigher) {
      setError('Giá vé mới không được cao hơn giá vé đã mua theo chính sách.')
      return
    }

    setSubmitting(true)
    setError(null)
    try {
      const res = await exchangeTicket({
        ve_id: ticket.ve_id,
        chuyen_xe_moi_id: selectedTrip.chuyen_xe_id,
        ghe_moi_id: selectedSeat.ghe_id,
      })
      setSuccessMsg(res.message || 'Đổi vé thành công!')
      setTimeout(() => {
        onSuccess()
        onClose()
      }, 1500)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Đổi vé thất bại.')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
      <div className="max-h-[90vh] w-full max-w-2xl overflow-y-auto rounded-xl bg-white p-6 shadow-xl">
        <div className="flex items-center justify-between border-b border-slate-200 pb-3">
          <h2 className="text-xl font-bold text-slate-800">
            Yêu cầu đổi vé — <span className="font-mono text-blue-600">{ticket.ve_id}</span>
          </h2>
          <button
            type="button"
            onClick={onClose}
            className="rounded p-1 text-slate-400 hover:bg-slate-100 hover:text-slate-600"
          >
            ✕
          </button>
        </div>

        {/* Thông tin vé cũ */}
        <div className="mt-4 rounded-lg bg-blue-50/70 p-3 text-sm text-blue-900 border border-blue-100">
          <p className="font-semibold text-blue-800">Vé hiện tại của bạn:</p>
          <div className="mt-1 grid grid-cols-2 gap-2 sm:grid-cols-4">
            <div>
              <span className="text-blue-600">Hành khách:</span> {ticket.ho_ten ?? '—'}
            </div>
            <div>
              <span className="text-blue-600">Ghế cũ:</span> {ticket.so_ghe}
            </div>
            <div>
              <span className="text-blue-600">Giá vé đã mua:</span> {formatCurrency(ticket.gia_ve)}
            </div>
            <div>
              <span className="text-blue-600">Tuyến:</span> {currentOrder?.chuyen.ten_tuyen ?? '—'}
            </div>
          </div>
        </div>

        {/* Chính sách đổi vé theo BPMN */}
        <div className="mt-3 rounded-lg bg-amber-50 p-3 text-xs text-amber-800 border border-amber-200">
          <p className="font-bold">Chính sách đổi vé:</p>
          <ul className="mt-1 list-disc list-inside space-y-0.5">
            <li>Chỉ đổi trước 24 giờ so với giờ khởi hành của chuyến cũ.</li>
            <li>Vé mới có giá trị $\le$ giá vé đã mua.</li>
            <li>Không hoàn tiền đối với vé đổi có giá trị thấp hơn vé đã mua.</li>
          </ul>
        </div>

        {/* Bước 1: Tìm chuyến mới */}
        <div className="mt-5 space-y-3">
          <h3 className="font-semibold text-slate-800">1. Chọn chuyến xe mới</h3>
          <form onSubmit={handleSearchTrips} className="grid grid-cols-1 gap-2 sm:grid-cols-4 items-end">
            <div>
              <label className="block text-xs font-medium text-slate-600">Điểm đi</label>
              <select
                value={diemDi}
                onChange={(e) => setDiemDi(e.target.value)}
                className="mt-1 w-full rounded border border-slate-300 px-2 py-1.5 text-sm"
              >
                {locations.diem_di.map((d) => (
                  <option key={d} value={d}>
                    {d}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-xs font-medium text-slate-600">Điểm đến</label>
              <select
                value={diemDen}
                onChange={(e) => setDiemDen(e.target.value)}
                className="mt-1 w-full rounded border border-slate-300 px-2 py-1.5 text-sm"
              >
                {locations.diem_den.map((d) => (
                  <option key={d} value={d}>
                    {d}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-xs font-medium text-slate-600">Ngày đi</label>
              <input
                type="date"
                value={ngay}
                onChange={(e) => setNgay(e.target.value)}
                className="mt-1 w-full rounded border border-slate-300 px-2 py-1.5 text-sm"
              />
            </div>
            <button
              type="submit"
              disabled={searchingTrips}
              className="rounded bg-blue-600 px-3 py-1.5 text-sm font-semibold text-white hover:bg-blue-700 disabled:opacity-50"
            >
              {searchingTrips ? 'Đang tìm…' : 'Tìm chuyến'}
            </button>
          </form>

          {searchError && <p className="text-xs text-red-600">{searchError}</p>}

          {trips.length > 0 && (
            <div className="max-h-48 overflow-y-auto space-y-2 border border-slate-200 rounded p-2">
              {trips.map((trip) => {
                const isSelected = selectedTrip?.chuyen_xe_id === trip.chuyen_xe_id
                return (
                  <div
                    key={trip.chuyen_xe_id}
                    onClick={() => handleSelectTrip(trip)}
                    className={`cursor-pointer rounded border p-2 text-sm transition-all ${
                      isSelected
                        ? 'border-blue-600 bg-blue-50/50'
                        : 'border-slate-200 hover:border-slate-300 hover:bg-slate-50'
                    }`}
                  >
                    <div className="flex justify-between font-medium">
                      <span>
                        {formatTime(trip.gio_di)} ({formatDate(trip.ngay_khoi_hanh)}) — {trip.ten_tuyen}
                      </span>
                      <span className="text-blue-700 font-semibold">{formatCurrency(trip.gia_ve)}</span>
                    </div>
                    <div className="text-xs text-slate-500 mt-0.5">
                      {trip.ten_loai_xe ?? `${trip.so_cho} chỗ`} • Còn {trip.so_ghe_trong} ghế trống
                    </div>
                  </div>
                )
              })}
            </div>
          )}
        </div>

        {/* Bước 2: Chọn ghế mới */}
        {selectedTrip && (
          <div className="mt-5 space-y-2">
            <h3 className="font-semibold text-slate-800">
              2. Chọn ghế mới trên chuyến {formatTime(selectedTrip.gio_di)}:
            </h3>
            {loadingSeats && <p className="text-xs text-slate-500">Đang tải sơ đồ ghế…</p>}
            {!loadingSeats && seats.length === 0 && (
              <p className="text-xs text-red-600">Chuyến xe này không còn ghế trống.</p>
            )}
            {!loadingSeats && seats.length > 0 && (
              <div className="flex flex-wrap gap-2">
                {seats.map((seat) => {
                  const isSeatSelected = selectedSeat?.ghe_id === seat.ghe_id
                  return (
                    <button
                      key={seat.ghe_id}
                      type="button"
                      onClick={() => setSelectedSeat(seat)}
                      className={`min-w-12 rounded border px-3 py-1.5 text-xs font-semibold transition-all ${
                        isSeatSelected
                          ? 'border-blue-600 bg-blue-600 text-white'
                          : 'border-slate-300 bg-white text-slate-800 hover:border-blue-400'
                      }`}
                    >
                      {seat.so_ghe}
                    </button>
                  )
                })}
              </div>
            )}
          </div>
        )}

        {/* Bước 3: Xem chênh lệch & xác nhận */}
        {selectedTrip && selectedSeat && (
          <div className="mt-5 space-y-3 border-t border-slate-200 pt-3">
            <h3 className="font-semibold text-slate-800">3. Thông tin chênh lệch & Xác nhận đổi:</h3>
            <div className="rounded-lg bg-slate-50 p-3 text-sm space-y-1">
              <div className="flex justify-between">
                <span className="text-slate-600">Giá vé cũ:</span>
                <span>{formatCurrency(ticket.gia_ve)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-600">Giá vé mới ({selectedSeat.so_ghe}):</span>
                <span className="font-semibold">{formatCurrency(selectedTrip.gia_ve)}</span>
              </div>
              <div className="flex justify-between border-t border-slate-200 pt-1 font-semibold">
                <span>Chênh lệch:</span>
                <span>{formatCurrency(Math.max(0, ticket.gia_ve - selectedTrip.gia_ve))}</span>
              </div>
              {isPriceHigher && (
                <p className="mt-2 text-xs text-red-600 font-medium">
                  ⚠️ Giá vé mới cao hơn vé đã mua. Chính sách không cho phép đổi sang vé giá cao hơn.
                </p>
              )}
            </div>
          </div>
        )}

        {/* Thông báo lỗi / thành công */}
        {error && (
          <div className="mt-4 rounded bg-red-50 p-2.5 text-xs text-red-700 border border-red-200">
            {error}
          </div>
        )}
        {successMsg && (
          <div className="mt-4 rounded bg-green-50 p-2.5 text-xs text-green-700 border border-green-200">
            {successMsg}
          </div>
        )}

        {/* Nút hành động */}
        <div className="mt-6 flex justify-end gap-3 border-t border-slate-200 pt-3">
          <button
            type="button"
            onClick={onClose}
            className="rounded border border-slate-300 px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50"
          >
            Đóng
          </button>
          <button
            type="button"
            disabled={!selectedTrip || !selectedSeat || isPriceHigher || submitting}
            onClick={handleConfirmExchange}
            className="rounded bg-blue-600 px-5 py-2 text-sm font-semibold text-white hover:bg-blue-700 disabled:opacity-50"
          >
            {submitting ? 'Đang chuyển tới n8n…' : 'Xác nhận đổi vé'}
          </button>
        </div>
      </div>
    </div>
  )
}
