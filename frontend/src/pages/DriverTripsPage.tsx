import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'

import { getDriverTrips, type DriverTrip } from '../services/driverService'
import { formatDate, formatTime, formatTripStatus } from '../utils/format'

type State =
  | { state: 'loading' }
  | { state: 'loaded'; data: DriverTrip[] }
  | { state: 'error'; message: string }

/** Tài xế: các chuyến được phân công; bấm vào chuyến để xem khách và thu tiền. */
export default function DriverTripsPage() {
  const [result, setResult] = useState<State>({ state: 'loading' })

  useEffect(() => {
    let cancelled = false
    getDriverTrips()
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
        <h1 className="text-xl sm:text-2xl font-bold tracking-tight text-slate-900">Chuyến của tôi</h1>
        <p className="mt-0.5 text-xs text-slate-500">Chuyến nhà xe đã phân công cho bạn.</p>
      </div>

      {result.state === 'loading' && (
        <p role="status" className="text-xs text-slate-600">
          Đang tải chuyến…
        </p>
      )}

      {result.state === 'error' && (
        <p role="alert" className="rounded-xl bg-rose-50 p-3 text-xs font-semibold text-rose-700 ring-1 ring-rose-200/70">
          {result.message}
        </p>
      )}

      {result.state === 'loaded' && result.data.length === 0 && (
        <p className="rounded-2xl border border-slate-200/90 bg-white p-5 text-center text-xs font-medium text-slate-600 shadow-2xs">
          Bạn chưa được phân công chuyến nào.
        </p>
      )}

      {result.state === 'loaded' && result.data.length > 0 && (
        <ul aria-label="Chuyến được phân công" className="space-y-3">
          {result.data.map((trip) => (
            <li key={trip.chuyen.chuyen_xe_id}>
              <Link
                to={`/tai-xe/chuyen/${encodeURIComponent(trip.chuyen.chuyen_xe_id)}`}
                className="block space-y-1.5 rounded-xl border border-slate-200/90 bg-white p-4 text-xs shadow-2xs hover:border-brand-300 hover:bg-brand-50/40"
              >
                <span className="flex flex-wrap items-center justify-between gap-1">
                  <span className="font-bold text-slate-900">{trip.chuyen.ten_tuyen}</span>
                  <span className="rounded-full bg-slate-100 px-2 py-0.5 font-semibold text-slate-700">
                    {formatTripStatus(trip.trang_thai)}
                  </span>
                </span>
                <span className="block text-slate-600">
                  {formatTime(trip.chuyen.gio_di)} ngày {formatDate(trip.chuyen.ngay_khoi_hanh)} · {trip.so_khach} khách
                </span>
              </Link>
            </li>
          ))}
        </ul>
      )}
    </section>
  )
}
