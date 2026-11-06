import { useEffect, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'

import BookerForm from '../components/BookerForm'
import CancelBookingButton from '../components/CancelBookingButton'
import SeatMap from '../components/SeatMap'
import { ApiError } from '../services/apiClient'
import { getBooking, holdSeats, type NguoiDat } from '../services/bookingService'
import { getTripSeats, type SeatMap as SeatMapData } from '../services/tripService'
import { clearStoredBooking, readStoredBooking } from '../utils/bookingStorage'
import { formatCurrency, formatDate, formatTime, formatVehicleType } from '../utils/format'

type SeatMapState =
  | { state: 'loading' }
  | { state: 'loaded'; data: SeatMapData }
  | { state: 'error'; message: string }

type HoldMode = 'seats' | 'whole'

function errorMessage(error: unknown): string {
  return error instanceof Error ? error.message : String(error)
}

export default function SeatSelectionPage() {
  const { id = '' } = useParams()
  const navigate = useNavigate()
  const [seatMap, setSeatMap] = useState<SeatMapState>({ state: 'loading' })
  const [reloadKey, setReloadKey] = useState(0)
  const [selected, setSelected] = useState<string[]>([])
  const [holdMode, setHoldMode] = useState<HoldMode | null>(null)
  const [submitting, setSubmitting] = useState(false)
  const [message, setMessage] = useState('')
  const [activeOrder, setActiveOrder] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false
    getTripSeats(id)
      .then((data) => {
        if (cancelled) return
        setSeatMap({ state: 'loaded', data })
        // Bỏ chọn các ghế không còn trống sau khi tải lại
        const free = new Set(data.ghe.filter((seat) => seat.trang_thai === 'TRONG').map((seat) => seat.ghe_id))
        setSelected((current) => current.filter((gheId) => free.has(gheId)))
      })
      .catch((error: unknown) => {
        if (!cancelled) setSeatMap({ state: 'error', message: errorMessage(error) })
      })
    return () => {
      cancelled = true
    }
  }, [id, reloadKey])

  // BR-BUS-18: mỗi tab 1 đơn đang giữ; đơn đã hết hạn hoặc không mở được thì bỏ
  useEffect(() => {
    const stored = readStoredBooking()
    if (!stored) return
    let cancelled = false
    getBooking(stored.ma_don)
      .then((booking) => {
        if (cancelled) return
        if (booking.dang_giu_cho) {
          setActiveOrder(booking.ma_don)
        } else {
          clearStoredBooking()
        }
      })
      .catch((error: unknown) => {
        if (!cancelled && error instanceof ApiError && error.status === 404) {
          clearStoredBooking()
        }
      })
    return () => {
      cancelled = true
    }
  }, [])

  if (seatMap.state !== 'loaded') {
    return (
      <section className="space-y-4">
        <h1 className="text-2xl font-bold text-brand-800">Chọn ghế</h1>
        {seatMap.state === 'loading' ? (
          <p role="status" className="text-slate-600">
            Đang tải sơ đồ ghế…
          </p>
        ) : (
          <div role="alert" className="flex items-center justify-between gap-2 rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700">
            <span>{seatMap.message}</span>
            <button type="button" onClick={() => setReloadKey((value) => value + 1)} className="font-medium underline">
              Thử lại
            </button>
          </div>
        )}
      </section>
    )
  }

  const { chuyen, ghe, co_the_dat: bookable } = seatMap.data
  const canHold = bookable && activeOrder === null
  const allFree = ghe.length > 0 && ghe.every((seat) => seat.trang_thai === 'TRONG')
  const selectedCodes = ghe.filter((seat) => selected.includes(seat.ghe_id)).map((seat) => seat.so_ghe)

  function toggle(gheId: string) {
    setMessage('')
    if (selected.includes(gheId)) {
      setSelected(selected.filter((value) => value !== gheId))
      return
    }
    // BR-BUS-15: tối đa bằng số chỗ của xe
    if (selected.length >= chuyen.so_cho) {
      setMessage(`Chỉ chọn được tối đa ${chuyen.so_cho} ghế.`)
      return
    }
    setSelected([...selected, gheId])
  }

  async function submitHold(nguoiDat: NguoiDat | null) {
    setSubmitting(true)
    setMessage('')
    try {
      const result = await holdSeats({
        chuyen_xe_id: chuyen.chuyen_xe_id,
        ...(holdMode === 'whole' ? { dat_ca_xe: true } : { ghe_ids: selected }),
        ...(nguoiDat ? { nguoi_dat: nguoiDat } : {}),
      })
      navigate(`/dat-ve/${encodeURIComponent(result.ma_don)}`)
    } catch (error: unknown) {
      setSubmitting(false)
      setMessage(errorMessage(error))
      // Ghế vừa bị người khác giữ: tải lại sơ đồ để thấy trạng thái mới
      if (error instanceof ApiError && error.status === 409) {
        setHoldMode(null)
        setReloadKey((value) => value + 1)
      }
    }
  }

  return (
    <section className="space-y-4">
      <h1 className="text-2xl font-bold text-brand-800">Chọn ghế</h1>

      <div className="space-y-1 rounded-xl border border-brand-100 bg-white shadow-sm p-4">
        <p className="text-lg font-semibold">{chuyen.ten_tuyen}</p>
        <p className="text-slate-700">
          {formatTime(chuyen.gio_di)} ngày {formatDate(chuyen.ngay_khoi_hanh)}
          {chuyen.gio_den ? ` → ${formatTime(chuyen.gio_den)}` : ''}
        </p>
        {chuyen.diem_trung_gian && <p className="text-sm text-slate-500">Qua: {chuyen.diem_trung_gian}</p>}
        <p className="text-sm text-slate-600">
          {formatVehicleType(chuyen.ten_loai_xe, chuyen.so_cho)} · {chuyen.so_cho} chỗ
        </p>
        <p className="font-semibold text-brand-700">
          {formatCurrency(chuyen.gia_ve)} <span className="text-sm font-normal text-slate-500">/ ghế</span>
        </p>
      </div>

      {!bookable && (
        <p role="status" className="rounded-lg bg-slate-100 px-3 py-2 text-slate-700">
          Chuyến này hiện không nhận đặt vé.
        </p>
      )}

      {activeOrder && (
        <div className="space-y-2 rounded-lg bg-amber-50 px-3 py-2 text-sm text-amber-800">
          <p role="status">Bạn đang có một đơn giữ ghế chưa hoàn tất. Mỗi lần chỉ giữ được một đơn.</p>
          <Link to={`/dat-ve/${encodeURIComponent(activeOrder)}`} className="block font-medium underline">
            Mở lại đơn {activeOrder}
          </Link>
          {/* Hủy đơn cũ để giữ ghế mới (BR-BUS-18, 33) */}
          <CancelBookingButton
            maDon={activeOrder}
            label="Hủy đơn cũ"
            onCancelled={() => {
              setActiveOrder(null)
              setReloadKey((value) => value + 1)
            }}
          />
        </div>
      )}

      {message && (
        <p role="alert" className="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700">
          {message}
        </p>
      )}

      <SeatMap seats={ghe} selected={selected} onToggle={toggle} disabled={!canHold || holdMode !== null} />

      {/* Tiền chỉ hiện giá mỗi ghế backend trả; tổng tiền do backend tính sau khi giữ ghế */}
      <div className="flex flex-col gap-3 rounded-2xl bg-white p-4 shadow-md ring-1 ring-brand-100 sm:flex-row sm:items-center sm:justify-between">
        <p className="flex items-center gap-3 text-slate-700">
          <span className="text-3xl font-bold text-brand-700">{String(selected.length).padStart(2, '0')}</span>
          <span>
            Đã chọn: <span className="font-semibold">{selected.length} ghế</span>
            {selectedCodes.length > 0 && ` (${selectedCodes.join(', ')})`}
            <span className="block text-sm text-slate-500">{formatCurrency(chuyen.gia_ve)} / ghế</span>
          </span>
        </p>
        {holdMode === null && (
          <div className="flex flex-col gap-2 sm:flex-row">
            <button
              type="button"
              disabled={!canHold || selected.length === 0}
              onClick={() => setHoldMode('seats')}
              className="rounded-lg bg-amber-400 px-5 py-2 font-semibold text-slate-900 shadow-sm hover:bg-amber-300 disabled:bg-slate-200 disabled:text-slate-500 disabled:shadow-none"
            >
              Giữ ghế
            </button>
            <button
              type="button"
              disabled={!canHold || !allFree}
              onClick={() => setHoldMode('whole')}
              className="rounded-lg border border-brand-600 px-5 py-2 font-semibold text-brand-700 hover:bg-brand-50 disabled:border-slate-300 disabled:text-slate-400"
            >
              Đặt cả xe
            </button>
          </div>
        )}
      </div>

      {holdMode !== null && (
        <div className="space-y-3 rounded-xl border border-brand-100 bg-white shadow-sm p-4">
          <h2 className="font-semibold">
            {holdMode === 'whole' ? `Đặt cả xe (${ghe.length} ghế)` : 'Thông tin người đặt'}
          </h2>
          <BookerForm
            onSubmit={(nguoiDat) => void submitHold(nguoiDat)}
            onCancel={() => setHoldMode(null)}
            submitting={submitting}
          />
        </div>
      )}
    </section>
  )
}
