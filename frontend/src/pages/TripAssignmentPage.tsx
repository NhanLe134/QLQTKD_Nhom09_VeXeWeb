import { useEffect, useId, useState } from 'react'

import { ApiError } from '../services/apiClient'
import {
  assignDriver,
  getDrivers,
  getOperatorTrips,
  type Driver,
  type OperatorTrip,
} from '../services/operatorService'
import { formatDate, formatTime, formatTripStatus, formatVehicleType, todayInVietnam } from '../utils/format'

type State =
  | { state: 'loading' }
  | { state: 'loaded'; trips: OperatorTrip[]; drivers: Driver[] }
  | { state: 'error'; message: string }

/** Nhà xe: chọn ngày → danh sách chuyến → chọn tài xế cho từng chuyến → Lưu. */
export default function TripAssignmentPage() {
  const [ngay, setNgay] = useState(() => todayInVietnam())
  const [result, setResult] = useState<State>({ state: 'loading' })
  const dateId = useId()

  useEffect(() => {
    if (!ngay) return
    let cancelled = false
    Promise.all([getOperatorTrips(ngay), getDrivers(ngay)])
      .then(([trips, drivers]) => {
        if (!cancelled) setResult({ state: 'loaded', trips, drivers })
      })
      .catch((error: unknown) => {
        if (!cancelled) setResult({ state: 'error', message: error instanceof Error ? error.message : String(error) })
      })
    return () => {
      cancelled = true
    }
  }, [ngay])

  function handleSaved(trip: OperatorTrip) {
    setResult((current) =>
      current.state === 'loaded'
        ? {
            ...current,
            trips: current.trips.map((item) =>
              item.chuyen.chuyen_xe_id === trip.chuyen.chuyen_xe_id ? trip : item,
            ),
          }
        : current,
    )
  }

  return (
    <section className="space-y-4">
      <div>
        <h1 className="text-xl sm:text-2xl font-bold tracking-tight text-slate-900">Phân công tài xế</h1>
        <p className="mt-0.5 text-xs text-slate-500">Chọn ngày, chọn tài xế cho từng chuyến rồi bấm Lưu.</p>
      </div>

      <div className="space-y-1 text-xs">
        <label htmlFor={dateId} className="font-semibold text-slate-700">
          Ngày khởi hành
        </label>
        <input
          id={dateId}
          type="date"
          value={ngay}
          onChange={(e) => {
            setNgay(e.target.value)
            setResult({ state: 'loading' })
          }}
          className="block w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 outline-none focus:border-brand-500 focus:ring-2 focus:ring-brand-100 sm:w-60"
        />
      </div>

      {result.state === 'loading' && ngay && (
        <p role="status" className="text-xs text-slate-600">
          Đang tải chuyến…
        </p>
      )}

      {result.state === 'error' && (
        <p role="alert" className="rounded-xl bg-rose-50 p-3 text-xs font-semibold text-rose-700 ring-1 ring-rose-200/70">
          {result.message}
        </p>
      )}

      {result.state === 'loaded' && result.trips.length === 0 && (
        <p className="rounded-2xl border border-slate-200/90 bg-white p-5 text-center text-xs font-medium text-slate-600 shadow-2xs">
          Không có chuyến nào trong ngày này.
        </p>
      )}

      {result.state === 'loaded' && result.trips.length > 0 && (
        <ul aria-label="Chuyến trong ngày" className="space-y-3">
          {result.trips.map((trip) => (
            <TripAssignmentCard
              key={trip.chuyen.chuyen_xe_id}
              trip={trip}
              drivers={result.drivers}
              onSaved={handleSaved}
            />
          ))}
        </ul>
      )}
    </section>
  )
}

type CardProps = {
  trip: OperatorTrip
  drivers: Driver[]
  onSaved: (trip: OperatorTrip) => void
}

function driverLabel(driver: Driver): string {
  return driver.ho_ten ? `${driver.ho_ten} (${driver.tai_xe_id})` : driver.tai_xe_id
}

function TripAssignmentCard({ trip, drivers, onSaved }: CardProps) {
  const [selected, setSelected] = useState(trip.tai_xe?.tai_xe_id ?? '')
  const [fieldError, setFieldError] = useState('')
  const [message, setMessage] = useState('')
  const [done, setDone] = useState('')
  const [saving, setSaving] = useState(false)
  const selectId = useId()
  const errorId = useId()
  const { chuyen } = trip
  // Tài xế hiện tại có thể không còn trong danh sách (đã nghỉ): vẫn hiện để không mất lựa chọn
  const options =
    trip.tai_xe && !drivers.some((d) => d.tai_xe_id === trip.tai_xe?.tai_xe_id) ? [trip.tai_xe, ...drivers] : drivers

  async function save() {
    if (!selected) {
      setFieldError('Vui lòng chọn tài xế')
      return
    }
    setSaving(true)
    setFieldError('')
    setMessage('')
    setDone('')
    try {
      const saved = await assignDriver(chuyen.chuyen_xe_id, selected)
      onSaved(saved)
      setDone(`Đã phân công ${saved.tai_xe ? driverLabel(saved.tai_xe) : ''}.`)
    } catch (error: unknown) {
      const detail = error instanceof Error ? error.message : String(error)
      if (error instanceof ApiError && error.field === 'tai_xe_id') setFieldError(detail)
      else setMessage(detail)
    } finally {
      setSaving(false)
    }
  }

  return (
    <li
      aria-label={`Chuyến ${chuyen.chuyen_xe_id}`}
      className="space-y-2.5 rounded-xl border border-slate-200/90 bg-white p-4 text-xs shadow-2xs"
    >
      <div className="flex flex-wrap items-center justify-between gap-1 border-b border-slate-100 pb-2">
        <p className="font-bold text-slate-900">{chuyen.ten_tuyen}</p>
        <p className="text-slate-500">
          {formatTime(chuyen.gio_di)}
          {chuyen.gio_den ? ` – ${formatTime(chuyen.gio_den)}` : ''} ngày {formatDate(chuyen.ngay_khoi_hanh)}
        </p>
      </div>
      <dl className="grid grid-cols-2 gap-x-3 gap-y-1.5">
        <dt className="text-slate-500">Mã chuyến</dt>
        <dd className="text-right font-mono font-semibold text-slate-800">{chuyen.chuyen_xe_id}</dd>
        <dt className="text-slate-500">Loại xe</dt>
        <dd className="text-right text-slate-800">{formatVehicleType(chuyen.ten_loai_xe, chuyen.so_cho)}</dd>
        <dt className="text-slate-500">Trạng thái</dt>
        <dd className="text-right font-semibold text-slate-800">{formatTripStatus(trip.trang_thai)}</dd>
        <dt className="text-slate-500">Tài xế hiện tại</dt>
        <dd className="text-right font-semibold text-slate-800">{trip.tai_xe ? driverLabel(trip.tai_xe) : 'Chưa phân công'}</dd>
      </dl>

      <div className="space-y-1">
        <label htmlFor={selectId} className="font-semibold text-slate-700">
          Chọn tài xế
        </label>
        <div className="flex flex-col gap-2 sm:flex-row">
          <select
            id={selectId}
            value={selected}
            onChange={(e) => {
              setSelected(e.target.value)
              setFieldError('')
              setDone('')
            }}
            aria-invalid={fieldError ? true : undefined}
            aria-describedby={fieldError ? errorId : undefined}
            className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 outline-none focus:border-brand-500 focus:ring-2 focus:ring-brand-100"
          >
            <option value="">— Chọn tài xế —</option>
            {options.map((driver) => (
              <option key={driver.tai_xe_id} value={driver.tai_xe_id}>
                {driverLabel(driver)}
              </option>
            ))}
          </select>
          <button
            type="button"
            onClick={save}
            disabled={saving}
            className="rounded-lg bg-brand-600 px-5 py-2 text-xs font-bold text-white shadow-2xs hover:bg-brand-700 disabled:opacity-50"
          >
            {saving ? 'Đang lưu…' : 'Lưu'}
          </button>
        </div>
        {fieldError && (
          <p id={errorId} role="alert" className="font-semibold text-rose-700">
            {fieldError}
          </p>
        )}
      </div>

      {message && (
        <p role="alert" className="font-semibold text-rose-700">
          {message}
        </p>
      )}
      {done && (
        <p role="status" className="font-semibold text-emerald-700">
          {done}
        </p>
      )}
    </li>
  )
}
