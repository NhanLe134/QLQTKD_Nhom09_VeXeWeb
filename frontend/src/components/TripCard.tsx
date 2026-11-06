import { Link } from 'react-router-dom'

import type { Trip } from '../services/tripService'
import { formatCurrency, formatTime, formatVehicleType } from '../utils/format'

type Props = {
  trip: Trip
}

// Thẻ chuyến xe nhỏ gọn, hiển thị thông tin lộ trình, giá và số chỗ
export default function TripCard({ trip }: Props) {
  const soldOut = trip.so_ghe_trong === 0
  const departure = formatTime(trip.gio_di)
  const arrival = trip.gio_den ? formatTime(trip.gio_den) : '--:--'

  return (
    <article
      aria-label={`Chuyến ${departure} ${trip.ten_tuyen}`}
      className="flex h-full flex-col justify-between rounded-xl border border-slate-200/90 bg-white p-3.5 shadow-2xs transition-all duration-150 hover:border-brand-300 hover:shadow-xs"
    >
      <div className="space-y-3">
        {/* Tuyến xe & Loại xe */}
        <div className="flex items-center justify-between gap-2 border-b border-slate-100 pb-2">
          <p className="text-sm font-bold text-slate-900 truncate">{trip.ten_tuyen}</p>
          <span className="shrink-0 rounded bg-slate-100 px-2 py-0.5 text-[11px] font-semibold text-slate-600">
            {formatVehicleType(trip.ten_loai_xe, trip.so_cho)}
          </span>
        </div>

        {/* Lộ trình và Giờ đi / Giờ đến */}
        <div className="flex items-start justify-between gap-2">
          <ol className="space-y-1 text-xs">
            <li className="flex items-start gap-2">
              <span aria-hidden="true" className="mt-1 h-2 w-2 shrink-0 rounded-full bg-emerald-500 ring-2 ring-emerald-100" />
              <div>
                <span className="block text-base font-extrabold leading-none text-slate-900">{departure}</span>
                <span className="text-[11px] font-medium text-slate-500">{trip.diem_di}</span>
              </div>
            </li>
            {trip.diem_trung_gian && (
              <li className="ml-1 border-l border-dashed border-slate-200 pl-3 py-0.5 text-[11px] text-slate-400">
                Qua: {trip.diem_trung_gian}
              </li>
            )}
            <li className="flex items-start gap-2">
              <span aria-hidden="true" className="mt-1 h-2 w-2 shrink-0 rounded-full bg-rose-500 ring-2 ring-rose-100" />
              <div>
                <span className="block text-base font-extrabold leading-none text-slate-900">{arrival}</span>
                <span className="text-[11px] font-medium text-slate-500">{trip.diem_den}</span>
              </div>
            </li>
          </ol>

          {/* Giá vé & Số ghế trống */}
          <div className="text-right shrink-0">
            <p className="text-lg font-black text-amber-600 leading-tight">{formatCurrency(trip.gia_ve)}</p>
            <p className="text-[10px] text-slate-400">/ ghế</p>
            <div className="mt-1">
              {soldOut ? (
                <span className="inline-block rounded bg-rose-50 px-1.5 py-0.5 text-[10px] font-bold text-rose-600 ring-1 ring-rose-200/60">
                  Hết ghế
                </span>
              ) : (
                <span className="inline-block rounded bg-emerald-50 px-1.5 py-0.5 text-[10px] font-bold text-emerald-700 ring-1 ring-emerald-200/60">
                  Còn {trip.so_ghe_trong} ghế trống
                </span>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Nút hành động */}
      <div className="mt-3 flex items-center justify-end border-t border-slate-100 pt-2.5">
        {soldOut ? (
          <button
            type="button"
            disabled
            className="w-full rounded-lg bg-slate-100 px-3 py-1.5 text-xs font-bold text-slate-400 cursor-not-allowed sm:w-auto"
          >
            Chọn chuyến
          </button>
        ) : (
          <Link
            to={`/chuyen/${encodeURIComponent(trip.chuyen_xe_id)}`}
            className="w-full rounded-lg bg-amber-400 px-3.5 py-1.5 text-xs font-bold text-slate-900 shadow-2xs transition-all hover:bg-amber-300 active:scale-[0.98] sm:w-auto text-center"
          >
            Chọn chuyến
          </Link>
        )}
      </div>
    </article>
  )
}
