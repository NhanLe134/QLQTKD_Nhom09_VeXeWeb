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
      <h1 className="text-2xl font-bold text-brand-800">Đặt vé thành công</h1>
      <p role="status" className="rounded-lg bg-green-50 px-3 py-2 font-medium text-green-700">
        Đơn đã được xác nhận.
        {payOnBoard && ` Vui lòng trả ${formatCurrency(booking.tong_tien)} cho tài xế khi lên xe.`}
      </p>
      <p className="text-slate-600">
        Mã đơn: <span className="font-semibold text-slate-900">{booking.ma_don}</span>
      </p>

      <div className="space-y-1 rounded-xl border border-brand-100 bg-white shadow-sm p-4">
        <p className="text-lg font-semibold">{chuyen.ten_tuyen}</p>
        <p className="text-slate-700">
          {formatTime(chuyen.gio_di)} ngày {formatDate(chuyen.ngay_khoi_hanh)}
        </p>
        <p className="text-sm text-slate-600">{formatVehicleType(chuyen.ten_loai_xe, chuyen.so_cho)}</p>
      </div>

      <TicketList tickets={tickets} />

      <p className="flex justify-between rounded-xl border border-brand-100 bg-white shadow-sm p-4 font-semibold">
        <span>Tổng tiền</span>
        <span data-testid="tong-tien">{formatCurrency(booking.tong_tien)}</span>
      </p>

      <div className="flex flex-col gap-2 sm:flex-row">
        {user?.vai_tro === 'KHACH' && (
          <Link
            to="/ve-cua-toi"
            className="rounded-lg bg-brand-700 px-4 py-2 text-center font-semibold text-white shadow-sm hover:bg-brand-800"
          >
            Vé của tôi
          </Link>
        )}
        <Link
          to="/"
          className="rounded-lg border border-slate-300 px-4 py-2 text-center font-medium text-slate-700 hover:bg-slate-50"
        >
          Về trang chủ
        </Link>
      </div>
    </section>
  )
}
