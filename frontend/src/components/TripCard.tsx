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
      className="flex h-full flex-col gap-3 rounded-2xl bg-white p-4 shadow-md ring-1 ring-brand-100"
    >
      <div className="flex items-start justify-between gap-3">
        {/* Giờ đi → giờ đến dạng dòng thời gian */}
        <ol className="space-y-1 text-sm">
          <li className="flex gap-2">
            <span aria-hidden="true" className="mt-1.5 h-2.5 w-2.5 shrink-0 rounded-full bg-green-500" />
            <span>
              <span className="block text-lg leading-tight font-bold">{departure}</span>
              <span className="text-slate-600">{trip.diem_di}</span>
            </span>
          </li>
          {trip.diem_trung_gian && (
            <li className="ml-1 border-l-2 border-dashed border-slate-300 pl-3 text-xs text-slate-500">
              Qua: {trip.diem_trung_gian}
            </li>
          )}
          <li className="flex gap-2">
            <span aria-hidden="true" className="mt-1.5 h-2.5 w-2.5 shrink-0 rounded-full bg-red-500" />
            <span>
              <span className="block text-lg leading-tight font-bold">{arrival}</span>
              <span className="text-slate-600">{trip.diem_den}</span>
            </span>
          </li>
        </ol>
        <div className="text-right">
          <p className="text-xl font-bold text-orange-600">{formatCurrency(trip.gia_ve)}</p>
          <p className="text-xs text-slate-500">/ ghế</p>
          <p className={`mt-1 text-sm font-medium ${soldOut ? 'text-red-600' : 'text-green-700'}`}>
            {soldOut ? 'Hết ghế' : `Còn ${trip.so_ghe_trong} ghế trống`}
          </p>
        </div>
      </div>

      <div className="flex items-end justify-between gap-3 border-t border-slate-100 pt-3">
        <div className="text-sm">
          <p className="font-semibold text-brand-800">{trip.ten_tuyen}</p>
          <p className="text-slate-600">{formatVehicleType(trip.ten_loai_xe, trip.so_cho)}</p>
        </div>
        {soldOut ? (
          <button
            type="button"
            disabled
            className="shrink-0 rounded-lg bg-slate-200 px-4 py-2 text-sm font-semibold text-slate-500"
          >
            Chọn chuyến
          </button>
        ) : (
          <Link
            to={`/chuyen/${encodeURIComponent(trip.chuyen_xe_id)}`}
            className="shrink-0 rounded-lg bg-amber-400 px-4 py-2 text-sm font-semibold text-slate-900 shadow-sm hover:bg-amber-300"
          >
            Chọn chuyến
          </Link>
        )}
      </div>
    </article>
  )
}
