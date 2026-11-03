import { Link } from 'react-router-dom'

import type { Trip } from '../services/tripService'
import { formatCurrency, formatTime, formatVehicleType } from '../utils/format'

type Props = {
  trip: Trip
}

// Chỉ hiển thị dữ liệu backend trả về: giá, số ghế trống không tính lại ở đây
export default function TripCard({ trip }: Props) {
  const soldOut = trip.so_ghe_trong === 0
  const departure = formatTime(trip.gio_di)
  const arrival = trip.gio_den ? formatTime(trip.gio_den) : '--:--'

  return (
    <article
      aria-label={`Chuyến ${departure} ${trip.ten_tuyen}`}
      className="flex flex-col gap-3 rounded-lg border border-slate-200 bg-white p-4 sm:flex-row sm:items-center sm:justify-between"
    >
      <div className="space-y-1">
        <p className="text-lg font-semibold">
          {departure} → {arrival}
        </p>
        <p className="text-slate-700">{trip.ten_tuyen}</p>
        {trip.diem_trung_gian && (
          <p className="text-sm text-slate-500">Qua: {trip.diem_trung_gian}</p>
        )}
        <p className="text-sm text-slate-600">{formatVehicleType(trip.ten_loai_xe, trip.so_cho)}</p>
      </div>
      <div className="space-y-2 sm:text-right">
        <p className="text-lg font-semibold text-blue-700">
          <span>{formatCurrency(trip.gia_ve)}</span> <span className="text-sm font-normal text-slate-500">/ ghế</span>
        </p>
        <p className={`text-sm ${soldOut ? 'text-red-600' : 'text-slate-600'}`}>
          {soldOut ? 'Hết ghế' : `Còn ${trip.so_ghe_trong} ghế trống`}
        </p>
        {soldOut ? (
          <button
            type="button"
            disabled
            className="w-full rounded-md bg-slate-300 px-4 py-2 font-medium text-slate-600 sm:w-auto"
          >
            Chọn chuyến
          </button>
        ) : (
          <Link
            to={`/chuyen/${encodeURIComponent(trip.chuyen_xe_id)}`}
            className="block w-full rounded-md bg-blue-700 px-4 py-2 text-center font-medium text-white hover:bg-blue-800 sm:inline-block sm:w-auto"
          >
            Chọn chuyến
          </Link>
        )}
      </div>
    </article>
  )
}
