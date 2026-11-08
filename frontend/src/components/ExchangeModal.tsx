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
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 p-4 backdrop-blur-2xs">
      <div className="max-h-[90vh] w-full max-w-xl overflow-y-auto rounded-2xl bg-white p-5 shadow-xl ring-1 ring-black/5">
        <div className="flex items-center justify-between border-b border-slate-100 pb-3">
          <h2 className="text-base font-bold text-slate-900">
            Yêu cầu đổi vé — <span className="font-mono font-bold text-brand-700">{ticket.ve_id}</span>
          </h2>
          <button
            type="button"
            onClick={onClose}
            className="flex h-7 w-7 items-center justify-center rounded-lg text-slate-400 hover:bg-slate-100 hover:text-slate-600 transition-colors"
          >
            ✕
          </button>
        </div>

        {/* Thông tin vé cũ */}
        <div className="mt-3 rounded-xl bg-brand-50/60 p-3 text-xs text-brand-900 border border-brand-100">
          <p className="font-bold text-brand-800">Vé hiện tại của bạn:</p>
          <div className="mt-1.5 grid grid-cols-2 gap-2 sm:grid-cols-4">
            <div>
              <span className="text-slate-500">Hành khách:</span> <strong className="text-slate-800 block truncate">{ticket.ho_ten ?? '—'}</strong>
            </div>
            <div>
              <span className="text-slate-500">Ghế cũ:</span> <strong className="text-slate-800 block">{ticket.so_ghe}</strong>
            </div>
            <div>
              <span className="text-slate-500">Giá vé đã mua:</span> <strong className="text-amber-600 block">{formatCurrency(ticket.gia_ve)}</strong>
            </div>
            <div>
              <span className="text-slate-500">Tuyến:</span> <strong className="text-slate-800 block truncate">{currentOrder?.chuyen.ten_tuyen ?? '—'}</strong>
            </div>
          </div>
        </div>

        {/* Chính sách đổi vé theo BPMN */}
        <div className="mt-2.5 rounded-xl bg-amber-50/70 p-2.5 text-[11px] text-amber-900 border border-amber-200/80">
          <p className="font-bold text-amber-800">Chính sách đổi vé:</p>
          <ul className="mt-0.5 list-disc list-inside space-y-0.5 text-amber-800/90">
            <li>Chỉ đổi trước 24 giờ so với giờ khởi hành của chuyến cũ.</li>
            <li>Vé mới có giá trị ≤ giá vé đã mua.</li>
            <li>Không hoàn tiền đối với vé đổi có giá trị thấp hơn vé đã mua.</li>
          </ul>
        </div>

        {/* Bước 1: Tìm chuyến mới */}
        <div className="mt-4 space-y-2.5">
          <h3 className="text-xs font-bold uppercase tracking-wider text-slate-700">1. Chọn chuyến xe mới</h3>
          <form onSubmit={handleSearchTrips} className="grid grid-cols-1 gap-2 sm:grid-cols-4 items-end">
            <div>
              <label className="block text-[11px] font-semibold text-slate-600">Điểm đi</label>
              <select
                value={diemDi}
                onChange={(e) => setDiemDi(e.target.value)}
                className="mt-1 w-full rounded-lg border border-slate-300 bg-white px-2 py-1.5 text-xs outline-none focus:border-brand-500"
              >
                {locations.diem_di.map((d) => (
                  <option key={d} value={d}>
                    {d}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-[11px] font-semibold text-slate-600">Điểm đến</label>
              <select
                value={diemDen}
                onChange={(e) => setDiemDen(e.target.value)}
                className="mt-1 w-full rounded-lg border border-slate-300 bg-white px-2 py-1.5 text-xs outline-none focus:border-brand-500"
              >
                {locations.diem_den.map((d) => (
                  <option key={d} value={d}>
                    {d}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-[11px] font-semibold text-slate-600">Ngày đi</label>
              <input
                type="date"
                value={ngay}
                onChange={(e) => setNgay(e.target.value)}
                className="mt-1 w-full rounded-lg border border-slate-300 bg-white px-2 py-1.5 text-xs outline-none focus:border-brand-500"
              />
            </div>
            <button
              type="submit"
              disabled={searchingTrips}
              className="inline-flex h-[32px] items-center justify-center rounded-lg bg-brand-600 px-3 text-xs font-bold text-white shadow-2xs hover:bg-brand-700 transition-all disabled:opacity-50"
            >
              {searchingTrips ? 'Đang tìm…' : 'Tìm chuyến'}
            </button>
          </form>

          {searchError && <p className="text-xs text-rose-600 font-medium">{searchError}</p>}

          {trips.length > 0 && (
            <div className="max-h-40 overflow-y-auto space-y-1.5 border border-slate-200 rounded-xl p-2 bg-slate-50/50">
              {trips.map((trip) => {
                const isSelected = selectedTrip?.chuyen_xe_id === trip.chuyen_xe_id
                return (
                  <div
                    key={trip.chuyen_xe_id}
                    onClick={() => handleSelectTrip(trip)}
                    className={`cursor-pointer rounded-lg border p-2 text-xs transition-all ${
                      isSelected
                        ? 'border-brand-500 bg-brand-50 text-brand-900 shadow-2xs'
                        : 'border-slate-200 bg-white hover:border-slate-300 hover:bg-slate-50'
                    }`}
                  >
                    <div className="flex justify-between font-bold">
                      <span>
                        {formatTime(trip.gio_di)} ({formatDate(trip.ngay_khoi_hanh)}) — {trip.ten_tuyen}
                      </span>
                      <span className="text-amber-600 font-extrabold">{formatCurrency(trip.gia_ve)}</span>
                    </div>
                    <div className="text-[11px] text-slate-500 mt-0.5">
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
          <div className="mt-4 space-y-2 border-t border-slate-100 pt-3">
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-700">
              2. Chọn ghế mới ({formatTime(selectedTrip.gio_di)}):
            </h3>
            {loadingSeats && <p className="text-xs text-slate-500">Đang tải sơ đồ ghế…</p>}
            {!loadingSeats && seats.length === 0 && (
              <p className="text-xs text-rose-600 font-medium">Chuyến xe này không còn ghế trống.</p>
            )}
            {!loadingSeats && seats.length > 0 && (
              <div className="flex flex-wrap gap-1.5">
                {seats.map((seat) => {
                  const isSeatSelected = selectedSeat?.ghe_id === seat.ghe_id
                  return (
                    <button
                      key={seat.ghe_id}
                      type="button"
                      onClick={() => setSelectedSeat(seat)}
                      className={`min-w-10 rounded-lg border px-2.5 py-1 text-xs font-bold transition-all ${
                        isSeatSelected
                          ? 'border-brand-600 bg-brand-600 text-white shadow-2xs'
                          : 'border-slate-300 bg-white text-slate-700 hover:border-brand-400'
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
          <div className="mt-4 space-y-2 border-t border-slate-100 pt-3">
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-700">3. Thông tin chênh lệch &amp; Xác nhận:</h3>
            <div className="rounded-xl bg-slate-50 p-3 text-xs space-y-1.5 border border-slate-200/80">
              <div className="flex justify-between">
                <span className="text-slate-500">Giá vé cũ:</span>
                <span className="font-semibold text-slate-800">{formatCurrency(ticket.gia_ve)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">Giá vé mới ({selectedSeat.so_ghe}):</span>
                <span className="font-bold text-slate-900">{formatCurrency(selectedTrip.gia_ve)}</span>
              </div>
              <div className="flex justify-between border-t border-slate-200 pt-1 font-bold">
                <span className="text-slate-700">Chênh lệch:</span>
                <span className="text-amber-600 font-extrabold">{formatCurrency(Math.max(0, ticket.gia_ve - selectedTrip.gia_ve))}</span>
              </div>
              {isPriceHigher && (
                <p className="mt-1.5 text-xs text-rose-600 font-semibold">
                  ⚠️ Giá vé mới cao hơn vé đã mua. Chính sách không cho phép đổi sang vé giá cao hơn.
                </p>
              )}
            </div>
          </div>
        )}

        {/* Thông báo lỗi / thành công */}
        {error && (
          <div className="mt-3 rounded-xl bg-rose-50 p-2.5 text-xs font-semibold text-rose-700 ring-1 ring-rose-200/70">
            {error}
          </div>
        )}
        {successMsg && (
          <div className="mt-3 rounded-xl bg-emerald-50 p-2.5 text-xs font-semibold text-emerald-700 ring-1 ring-emerald-200/70">
            {successMsg}
          </div>
        )}

        {/* Nút hành động */}
        <div className="mt-5 flex justify-end gap-2 border-t border-slate-100 pt-3">
          <button
            type="button"
            onClick={onClose}
            className="rounded-lg border border-slate-300 px-3.5 py-1.5 text-xs font-semibold text-slate-700 hover:bg-slate-50 transition-colors"
          >
            Đóng
          </button>
          <button
            type="button"
            disabled={!selectedTrip || !selectedSeat || isPriceHigher || submitting}
            onClick={handleConfirmExchange}
            className="rounded-lg bg-brand-600 px-4 py-1.5 text-xs font-bold text-white shadow-2xs hover:bg-brand-700 transition-all disabled:opacity-50"
          >
            {submitting ? 'Đang chuyển tới n8n…' : 'Xác nhận đổi vé'}
          </button>
        </div>
      </div>
    </div>
  )
}
