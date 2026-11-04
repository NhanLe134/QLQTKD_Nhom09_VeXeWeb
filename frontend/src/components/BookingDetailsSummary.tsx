import type { Booking } from '../services/bookingService'

type Props = {
  booking: Booking
  onEdit: () => void
}

/** Tóm tắt sau khi lưu: hiển thị đúng chuỗi backend trả về, không tự ghép. */
export default function BookingDetailsSummary({ booking, onEdit }: Props) {
  const tickets = booking.ve.filter((ve) => ve.trang_thai_ve !== 'DA_HUY')
  return (
    <section aria-label="Tóm tắt thông tin" className="space-y-3">
      <p role="status" className="rounded-md bg-green-50 px-3 py-2 text-sm font-medium text-green-700">
        Đã lưu thông tin hành khách.
      </p>
      <ul aria-label="Hành khách" className="divide-y divide-slate-100">
        {tickets.map((ve) => (
          <li key={ve.ve_id} className="py-1">
            <span className="font-medium">Ghế {ve.so_ghe}:</span> {ve.ho_ten} · {ve.so_dien_thoai}
          </li>
        ))}
      </ul>
      <dl className="grid grid-cols-[auto_1fr] gap-x-3 gap-y-1 text-sm">
        <dt className="text-slate-500">Điểm đón</dt>
        <dd data-testid="tom-tat-diem-don">{booking.diem_don?.chuoi}</dd>
        <dt className="text-slate-500">Điểm trả</dt>
        <dd data-testid="tom-tat-diem-tra">{booking.diem_tra?.chuoi}</dd>
      </dl>
      <div className="flex flex-col gap-2 sm:flex-row">
        {/* Task #10: chọn phương thức thanh toán */}
        <button
          type="button"
          disabled
          className="rounded-md bg-blue-700 px-4 py-2 font-medium text-white disabled:bg-slate-400"
        >
          Tiếp tục thanh toán
        </button>
        <button
          type="button"
          onClick={onEdit}
          className="rounded-md border border-slate-300 px-4 py-2 font-medium text-slate-700 hover:bg-slate-50"
        >
          Sửa
        </button>
      </div>
    </section>
  )
}
