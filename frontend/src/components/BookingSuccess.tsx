import { Link } from 'react-router-dom'

import { useAuth } from '../hooks/useAuth'
import type { Booking } from '../services/bookingService'
import { formatCurrency, formatDate, formatTime, formatVehicleType } from '../utils/format'
import TicketList from './TicketList'

/** Màn hình đặt vé thành công (BR-BUS-35): vé gom theo mã đơn, tổng tiền do backend tính. */
export default function BookingSuccess({ booking }: { booking: Booking }) {
  const { user } = useAuth()
  const { chuyen } = booking
  const tickets = booking.ve.filter((ve) => ve.trang_thai_ve === 'DA_XAC_NHAN')
  const payOnBoard = tickets.length > 0 && tickets.every((ve) => ve.trang_thai_thanh_toan === 'CHO_THU_TIEN_MAT')

  return (
    <section className="space-y-4">
      <div className="flex flex-col gap-1 sm:flex-row sm:items-center sm:justify-between">
        <h1 className="text-xl sm:text-2xl font-bold tracking-tight text-slate-900">Đặt vé thành công</h1>
        <p className="text-xs font-semibold text-slate-500">
          Mã đơn: <span className="font-mono font-bold text-slate-900">{booking.ma_don}</span>
        </p>
      </div>

      <div role="status" className="rounded-xl bg-emerald-50 p-3.5 text-xs sm:text-sm font-semibold text-emerald-800 ring-1 ring-emerald-200/70">
        Đơn đã được xác nhận.
        {payOnBoard && ` Vui lòng trả ${formatCurrency(booking.tong_tien)} cho tài xế khi lên xe.`}
      </div>

      <div className="rounded-2xl border border-slate-200/90 bg-white p-4 shadow-2xs space-y-1">
        <p className="text-sm font-bold text-slate-900">{chuyen.ten_tuyen}</p>
        <p className="text-xs text-slate-600">
          {formatTime(chuyen.gio_di)} ngày {formatDate(chuyen.ngay_khoi_hanh)}
        </p>
        <p className="text-[11px] text-slate-500">{formatVehicleType(chuyen.ten_loai_xe, chuyen.so_cho)}</p>
      </div>

      <TicketList tickets={tickets} />

      <div className="flex justify-between items-center rounded-2xl border border-slate-200/90 bg-white p-4 shadow-2xs text-xs font-bold text-slate-800">
        <span>Tổng tiền</span>
        <span data-testid="tong-tien" className="text-base font-black text-amber-600">{formatCurrency(booking.tong_tien)}</span>
      </div>

      <div className="flex flex-wrap items-center gap-2 pt-1">
        {user?.vai_tro === 'KHACH' && (
          <Link
            to="/ve-cua-toi"
            className="rounded-lg bg-brand-600 px-4 py-2 text-center text-xs font-bold text-white shadow-2xs transition-all hover:bg-brand-700 active:scale-[0.98]"
          >
            Vé của tôi
          </Link>
        )}
        <Link
          to="/"
          className="rounded-lg border border-slate-300 bg-white px-4 py-2 text-center text-xs font-semibold text-slate-700 hover:bg-slate-50 transition-colors"
        >
          Về trang chủ
        </Link>
      </div>
    </section>
  )
}
