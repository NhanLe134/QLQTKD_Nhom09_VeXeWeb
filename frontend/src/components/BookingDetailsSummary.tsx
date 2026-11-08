import type { Booking } from '../services/bookingService'

type Props = {
  booking: Booking
  onEdit: () => void
  /** Sang bước chọn phương thức thanh toán */
  onContinue: () => void
}

/** Tóm tắt sau khi lưu: hiển thị đúng chuỗi backend trả về, không tự ghép. */
export default function BookingDetailsSummary({ booking, onEdit, onContinue }: Props) {
  const tickets = booking.ve.filter((ve) => ve.trang_thai_ve !== 'DA_HUY')
  return (
    <section aria-label="Tóm tắt thông tin" className="space-y-3">
      <p role="status" className="rounded-lg bg-emerald-50 px-3 py-1.5 text-xs font-semibold text-emerald-700 ring-1 ring-emerald-200/60">
        Đã lưu thông tin hành khách.
      </p>
      <div className="rounded-xl border border-slate-200/90 bg-slate-50/50 p-3">
        <ul aria-label="Hành khách" className="divide-y divide-slate-200/60 text-xs">
          {tickets.map((ve) => (
            <li key={ve.ve_id} className="py-1.5 flex items-center justify-between">
              <span className="font-bold text-slate-800">Ghế {ve.so_ghe}:</span>
              <span className="text-slate-600">{ve.ho_ten} · {ve.so_dien_thoai}</span>
            </li>
          ))}
        </ul>
        <dl className="mt-2 grid grid-cols-[auto_1fr] gap-x-3 gap-y-1.5 border-t border-slate-200/60 pt-2 text-xs">
          <dt className="text-slate-400 font-medium">Điểm đón</dt>
          <dd data-testid="tom-tat-diem-don" className="font-semibold text-slate-800">{booking.diem_don?.chuoi}</dd>
          <dt className="text-slate-400 font-medium">Điểm trả</dt>
          <dd data-testid="tom-tat-diem-tra" className="font-semibold text-slate-800">{booking.diem_tra?.chuoi}</dd>
        </dl>
      </div>

      <div className="flex flex-wrap items-center gap-2 pt-1">
        <button
          type="button"
          onClick={onContinue}
          disabled={!booking.da_nhap_thong_tin}
          className="rounded-lg bg-brand-600 px-4 py-2 text-xs font-bold text-white shadow-2xs transition-all hover:bg-brand-700 active:scale-[0.98] disabled:bg-slate-300"
        >
          Tiếp tục thanh toán
        </button>
        <button
          type="button"
          onClick={onEdit}
          className="rounded-lg border border-slate-300 bg-white px-3.5 py-2 text-xs font-semibold text-slate-700 transition-colors hover:bg-slate-50"
        >
          Sửa
        </button>
      </div>
    </section>
  )
}
