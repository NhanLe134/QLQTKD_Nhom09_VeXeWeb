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

// Kết quả gắn với khóa tìm kiếm: khóa trên URL đổi thì kết quả cũ tự thành "đang tải"
type SearchOutcome =
  | { key: string; state: 'done'; data: TripSearchResult }
  | { key: string; state: 'error'; message: string }

function errorMessage(error: unknown): string {
  return error instanceof Error ? error.message : String(error)
}

function SuggestionList({ trips, onPick }: { trips: Trip[]; onPick: (ngay: string) => void }) {
  return (
    <div className="space-y-2">
      <p className="font-medium">Gợi ý chuyến cùng tuyến ngày lân cận:</p>
      <ul className="space-y-2">
        {trips.map((trip) => (
          <li key={trip.chuyen_xe_id}>
            <button
              type="button"
              onClick={() => onPick(trip.ngay_khoi_hanh)}
              className="w-full rounded-lg border border-brand-200 bg-brand-50 px-3 py-2 text-left text-sm hover:bg-brand-100"
            >
              <span className="font-semibold">Ngày {formatDate(trip.ngay_khoi_hanh)}</span>
              {' · '}
              {formatTime(trip.gio_di)} · {formatVehicleType(trip.ten_loai_xe, trip.so_cho)} ·{' '}
              {formatCurrency(trip.gia_ve)} / ghế ·{' '}
              {trip.so_ghe_trong > 0 ? `Còn ${trip.so_ghe_trong} ghế trống` : 'Hết ghế'}
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
    // Tham số nằm trên URL để tải lại trang vẫn giữ kết quả
    setSearchParams({ di: next.diemDi, den: next.diemDen, ngay: next.ngay })
  }

  function retryLocations() {
    setLocations({ state: 'loading' })
    setLocationsAttempt((value) => value + 1)
  }

  const current = outcome?.key === searchKey ? outcome : null

  return (
    <section className="space-y-4">
      <h1 className="text-2xl font-bold text-brand-800">Tìm chuyến</h1>

      {locations.state === 'error' && (
        <div role="alert" className="flex items-center justify-between gap-2 rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700">
          <span>Không tải được danh sách điểm đi, điểm đến: {locations.message}</span>
          <button type="button" onClick={retryLocations} className="font-medium underline">
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
        <p role="status" className="text-slate-600">
          Đang tìm chuyến…
        </p>
      )}

      {current?.state === 'error' && (
        <div role="alert" className="flex items-center justify-between gap-2 rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700">
          <span>{current.message}</span>
          <button type="button" onClick={() => setSearchAttempt((value) => value + 1)} className="font-medium underline">
            Thử lại
          </button>
        </div>
      )}

      {current?.state === 'done' && current.data.chuyen.length > 0 && (
        <div className="space-y-3">
          <p className="text-sm text-slate-600">
            {current.data.chuyen.length} chuyến ngày {formatDate(ngay)}
          </p>
          <ul className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {current.data.chuyen.map((trip) => (
              <li key={trip.chuyen_xe_id}>
                <TripCard trip={trip} />
              </li>
            ))}
          </ul>
        </div>
      )}

      {current?.state === 'done' && current.data.chuyen.length === 0 && (
        <div className="space-y-3 rounded-xl border border-brand-100 bg-white shadow-sm p-4">
          <p role="status" className="font-medium">
            Không có chuyến phù hợp ngày {formatDate(ngay)}.
          </p>
          {current.data.goi_y.length > 0 ? (
            <SuggestionList trips={current.data.goi_y} onPick={(nearbyDay) => search({ ...query, ngay: nearbyDay })} />
          ) : (
            <p className="text-sm text-slate-600">Không có chuyến cùng tuyến vào ngày trước hoặc sau.</p>
          )}
        </div>
      )}
    </section>
  )
}
