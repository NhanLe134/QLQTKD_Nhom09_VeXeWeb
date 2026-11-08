import { useEffect, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'

import BookerForm from '../components/BookerForm'
import CancelBookingButton from '../components/CancelBookingButton'
import SeatMap from '../components/SeatMap'
import { ApiError } from '../services/apiClient'
import { getBooking, holdSeats, type NguoiDatInput } from '../services/bookingService'
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
      <section className="space-y-6">
        <div>
          <h1 className="text-2xl font-extrabold tracking-tight text-slate-900 sm:text-3xl">Chọn ghế</h1>
        </div>
        {seatMap.state === 'loading' ? (
          <div className="flex items-center justify-center py-12">
            <p role="status" className="inline-flex items-center gap-2.5 rounded-xl bg-white px-5 py-3 text-sm font-semibold text-slate-600 shadow-2xs border border-slate-200/80">
              <span className="h-4 w-4 animate-spin rounded-full border-2 border-brand-600 border-t-transparent" />
              Đang tải sơ đồ ghế…
            </p>
          </div>
        ) : (
          <div role="alert" className="flex items-center justify-between gap-3 rounded-2xl bg-rose-50 p-4 text-sm text-rose-800 ring-1 ring-rose-200/70">
            <span>{seatMap.message}</span>
            <button type="button" onClick={() => setReloadKey((value) => value + 1)} className="font-bold underline hover:no-underline">
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

  async function submitHold(nguoiDat: NguoiDatInput | null) {
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
    <section className="space-y-6">
      <div>
        <h1 className="text-2xl font-extrabold tracking-tight text-slate-900 sm:text-3xl">Chọn ghế</h1>
        <p className="mt-1 text-sm text-slate-500">Chọn vị trí ngồi yêu thích và tiến hành giữ chỗ.</p>
      </div>

      {/* Thông tin chuyến xe */}
      <div className="rounded-3xl border border-slate-200/90 bg-white p-5 shadow-xs sm:p-6">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between border-b border-slate-100 pb-4">
          <div>
            <p className="text-lg font-bold text-slate-900">{chuyen.ten_tuyen}</p>
            <p className="text-sm font-medium text-slate-600">
              {formatTime(chuyen.gio_di)} ngày {formatDate(chuyen.ngay_khoi_hanh)}
              {chuyen.gio_den ? ` → ${formatTime(chuyen.gio_den)}` : ''}
            </p>
            {chuyen.diem_trung_gian && <p className="text-xs text-slate-400 mt-0.5">Qua: {chuyen.diem_trung_gian}</p>}
          </div>
          <div className="text-left sm:text-right">
            <span className="inline-flex items-center rounded-lg bg-slate-100 px-2.5 py-1 text-xs font-semibold text-slate-600 mb-1">
              {formatVehicleType(chuyen.ten_loai_xe, chuyen.so_cho)} · {chuyen.so_cho} chỗ
            </span>
            <p className="font-extrabold text-amber-600 text-lg sm:text-xl">
              {formatCurrency(chuyen.gia_ve)} <span className="text-xs font-normal text-slate-400">/ ghế</span>
            </p>
          </div>
        </div>
      </div>

      {!bookable && (
        <p role="status" className="rounded-2xl bg-slate-100 p-4 text-center text-sm font-semibold text-slate-600">
          Chuyến này hiện không nhận đặt vé.
        </p>
      )}

      {activeOrder && (
        <div className="space-y-3 rounded-2xl border border-amber-200 bg-amber-50/80 p-4 text-sm text-amber-900">
          <p role="status" className="font-semibold">
            Bạn đang có một đơn giữ ghế chưa hoàn tất. Mỗi lần chỉ giữ được một đơn.
          </p>
          <div className="flex flex-wrap items-center gap-3">
            <Link
              to={`/dat-ve/${encodeURIComponent(activeOrder)}`}
              className="font-bold text-brand-700 underline hover:no-underline"
            >
              Mở lại đơn {activeOrder}
            </Link>
            <CancelBookingButton
              maDon={activeOrder}
              label="Hủy đơn cũ"
              onCancelled={() => {
                setActiveOrder(null)
                setReloadKey((value) => value + 1)
              }}
            />
          </div>
        </div>
      )}

      {message && (
        <p role="alert" className="rounded-2xl bg-rose-50 p-4 text-sm font-semibold text-rose-700 ring-1 ring-rose-200/70">
          {message}
        </p>
      )}

      <SeatMap seats={ghe} selected={selected} onToggle={toggle} disabled={!canHold || holdMode !== null} />

      {/* Thanh tổng kết số ghế đã chọn */}
      <div className="flex flex-col gap-4 rounded-3xl border border-slate-200/90 bg-white p-5 shadow-xs sm:flex-row sm:items-center sm:justify-between">
        <div className="flex items-center gap-3.5">
          <span className="flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl bg-brand-50 text-2xl font-black text-brand-700 ring-1 ring-brand-100">
            {String(selected.length).padStart(2, '0')}
          </span>
          <div>
            <p className="text-sm font-bold text-slate-900">
              Đã chọn: <span className="font-extrabold text-brand-700">{selected.length} ghế</span>
              {selectedCodes.length > 0 && ` (${selectedCodes.join(', ')})`}
            </p>
            <span className="block text-xs font-medium text-slate-500">{formatCurrency(chuyen.gia_ve)} / ghế</span>
          </div>
        </div>

        {holdMode === null && (
          <div className="flex flex-col gap-2.5 sm:flex-row">
            <button
              type="button"
              disabled={!canHold || selected.length === 0}
              onClick={() => setHoldMode('seats')}
              className="rounded-xl bg-amber-400 px-6 py-2.5 text-sm font-bold text-slate-900 shadow-2xs transition-all hover:bg-amber-300 active:scale-[0.98] disabled:bg-slate-100 disabled:text-slate-400 disabled:shadow-none"
            >
              Giữ ghế
            </button>
            <button
              type="button"
              disabled={!canHold || !allFree}
              onClick={() => setHoldMode('whole')}
              className="rounded-xl border border-brand-600 px-6 py-2.5 text-sm font-bold text-brand-700 transition-colors hover:bg-brand-50 active:scale-[0.98] disabled:border-slate-200 disabled:text-slate-300"
            >
              Đặt cả xe
            </button>
          </div>
        )}
      </div>

      {holdMode !== null && (
        <div className="space-y-4 rounded-3xl border border-slate-200/90 bg-white p-6 shadow-xs">
          <h2 className="text-base font-bold text-slate-900 border-b border-slate-100 pb-3">
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
