import { useEffect, useState } from 'react'
import { useSearchParams } from 'react-router-dom'

import TripCard from '../components/TripCard'
import TripSearchForm from '../components/TripSearchForm'
import {
  getLocations,
  type Locations,
  searchTrips,
  type Trip,
  type TripSearchQuery,
  type TripSearchResult,
} from '../services/tripService'
import { formatCurrency, formatDate, formatTime, formatVehicleType } from '../utils/format'

type LocationsState =
  | { state: 'loading' }
  | { state: 'loaded'; data: Locations }
  | { state: 'error'; message: string }

type SearchOutcome =
  | { key: string; state: 'done'; data: TripSearchResult }
  | { key: string; state: 'error'; message: string }

function errorMessage(error: unknown): string {
  return error instanceof Error ? error.message : String(error)
}

function SuggestionList({ trips, onPick }: { trips: Trip[]; onPick: (ngay: string) => void }) {
  return (
    <div className="space-y-2 pt-1">
      <p className="text-xs font-bold text-slate-700">Gợi ý chuyến cùng tuyến ngày lân cận:</p>
      <ul className="space-y-1.5">
        {trips.map((trip) => (
          <li key={trip.chuyen_xe_id}>
            <button
              type="button"
              onClick={() => onPick(trip.ngay_khoi_hanh)}
              className="w-full rounded-lg border border-brand-200/80 bg-brand-50/50 px-3 py-2 text-left text-xs transition-all hover:bg-brand-100/70"
            >
              <div className="flex flex-wrap items-center justify-between gap-2">
                <div>
                  <span className="font-bold text-brand-900">Ngày {formatDate(trip.ngay_khoi_hanh)}</span>
                  {' · '}
                  <span className="font-semibold text-slate-800">{formatTime(trip.gio_di)}</span>
                  {' · '}
                  <span className="text-slate-600">{formatVehicleType(trip.ten_loai_xe, trip.so_cho)}</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="font-bold text-amber-600">{formatCurrency(trip.gia_ve)} / ghế</span>
                  <span className={`text-[11px] font-semibold ${trip.so_ghe_trong > 0 ? 'text-emerald-700' : 'text-slate-400'}`}>
                    {trip.so_ghe_trong > 0 ? `Còn ${trip.so_ghe_trong} ghế trống` : 'Hết ghế'}
                  </span>
                </div>
              </div>
            </button>
          </li>
        ))}
      </ul>
    </div>
  )
}

export default function TripSearchPage() {
  const [searchParams, setSearchParams] = useSearchParams()
  const query: TripSearchQuery = {
    diemDi: searchParams.get('di') ?? '',
    diemDen: searchParams.get('den') ?? '',
    ngay: searchParams.get('ngay') ?? '',
  }
  const { diemDi, diemDen, ngay } = query
  const hasQuery = Boolean(diemDi && diemDen && ngay)

  const [locations, setLocations] = useState<LocationsState>({ state: 'loading' })
  const [locationsAttempt, setLocationsAttempt] = useState(0)
  const [searchAttempt, setSearchAttempt] = useState(0)
  const [outcome, setOutcome] = useState<SearchOutcome | null>(null)

  const queryKey = JSON.stringify([diemDi, diemDen, ngay])
  const searchKey = `${queryKey}#${searchAttempt}`

  useEffect(() => {
    let cancelled = false
    getLocations()
      .then((data) => {
        if (!cancelled) setLocations({ state: 'loaded', data })
      })
      .catch((error: unknown) => {
        if (!cancelled) setLocations({ state: 'error', message: errorMessage(error) })
      })
    return () => {
      cancelled = true
    }
  }, [locationsAttempt])

  useEffect(() => {
    if (!hasQuery) return
    let cancelled = false
    searchTrips({ diemDi, diemDen, ngay })
      .then((data) => {
        if (!cancelled) setOutcome({ key: searchKey, state: 'done', data })
      })
      .catch((error: unknown) => {
        if (!cancelled) setOutcome({ key: searchKey, state: 'error', message: errorMessage(error) })
      })
    return () => {
      cancelled = true
    }
  }, [hasQuery, diemDi, diemDen, ngay, searchKey])

  function search(next: TripSearchQuery) {
    setSearchParams({ di: next.diemDi, den: next.diemDen, ngay: next.ngay })
  }

  function retryLocations() {
    setLocations({ state: 'loading' })
    setLocationsAttempt((value) => value + 1)
  }

  const current = outcome?.key === searchKey ? outcome : null

  return (
    <section className="space-y-4">
      <div>
        <h1 className="text-xl sm:text-2xl font-bold tracking-tight text-slate-900">Tìm chuyến</h1>
        <p className="mt-0.5 text-xs text-slate-500">Tra cứu lịch trình xe và giá vé các tuyến trong ngày.</p>
      </div>

      {locations.state === 'error' && (
        <div role="alert" className="flex items-center justify-between gap-3 rounded-xl bg-rose-50 p-3 text-xs text-rose-800 ring-1 ring-rose-200/70">
          <span>Không tải được danh sách điểm đi, điểm đến: {locations.message}</span>
          <button type="button" onClick={retryLocations} className="font-bold underline hover:no-underline">
            Thử lại
          </button>
        </div>
      )}

      <TripSearchForm
        key={queryKey}
        locations={locations.state === 'loaded' ? locations.data : null}
        initialValues={query}
        onSearch={search}
      />

      {hasQuery && !current && (
        <div className="flex items-center justify-center py-8">
          <p role="status" className="inline-flex items-center gap-2 rounded-lg bg-white px-4 py-2 text-xs font-medium text-slate-600 shadow-2xs border border-slate-200/80">
            <span className="h-3.5 w-3.5 animate-spin rounded-full border-2 border-brand-600 border-t-transparent" />
            Đang tìm chuyến…
          </p>
        </div>
      )}

      {current?.state === 'error' && (
        <div role="alert" className="flex items-center justify-between gap-3 rounded-xl bg-rose-50 p-3 text-xs text-rose-800 ring-1 ring-rose-200/70">
          <span>{current.message}</span>
          <button type="button" onClick={() => setSearchAttempt((value) => value + 1)} className="font-bold underline hover:no-underline">
            Thử lại
          </button>
        </div>
      )}

      {current?.state === 'done' && current.data.chuyen.length > 0 && (
        <div className="space-y-3">
          <p className="text-xs font-bold uppercase tracking-wider text-slate-500">
            {current.data.chuyen.length} chuyến ngày {formatDate(ngay)}
          </p>
          <ul className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {current.data.chuyen.map((trip) => (
              <li key={trip.chuyen_xe_id}>
                <TripCard trip={trip} />
              </li>
            ))}
          </ul>
        </div>
      )}

      {current?.state === 'done' && current.data.chuyen.length === 0 && (
        <div className="space-y-2.5 rounded-2xl border border-slate-200/90 bg-white p-4 shadow-2xs">
          <p role="status" className="text-sm font-bold text-slate-800">
            Không có chuyến phù hợp ngày {formatDate(ngay)}.
          </p>
          {current.data.goi_y.length > 0 ? (
            <SuggestionList trips={current.data.goi_y} onPick={(nearbyDay) => search({ ...query, ngay: nearbyDay })} />
          ) : (
            <p className="text-xs text-slate-500">Không có chuyến cùng tuyến vào ngày trước hoặc sau.</p>
          )}
        </div>
      )}
    </section>
  )
}
