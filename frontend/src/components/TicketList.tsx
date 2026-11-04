import type { Ticket } from '../services/bookingService'
import { formatCurrency, formatPaymentStatus } from '../utils/format'

type Props = {
  tickets: Ticket[]
  /** Nhãn của danh sách cho trình đọc màn hình */
  label?: string
}

/**
 * Vé điện tử: mỗi ghế một vé, mã vé là `ve_id` (BR-BUS-35). Dùng ở màn đặt vé thành công,
 * "Vé của tôi" và "Tra cứu vé" (task #13). Chỉ hiển thị dữ liệu backend trả về.
 */
export default function TicketList({ tickets, label = 'Vé điện tử' }: Props) {
  return (
    <ul aria-label={label} className="space-y-3">
      {tickets.map((ve) => (
        <li
          key={ve.ve_id}
          aria-label={`Vé ${ve.ve_id}`}
          className="rounded-lg border border-dashed border-slate-300 bg-white p-3"
        >
          <div className="flex items-baseline justify-between gap-2">
            <p className="font-semibold">
              Mã vé: <span className="font-mono">{ve.ve_id}</span>
            </p>
            <p className="text-sm font-medium text-slate-700">Ghế {ve.so_ghe}</p>
          </div>
          <dl className="mt-2 grid grid-cols-[auto_1fr] gap-x-3 gap-y-1 text-sm">
            <dt className="text-slate-500">Hành khách</dt>
            <dd>{ve.ho_ten ?? '—'}</dd>
            <dt className="text-slate-500">Điểm đón</dt>
            <dd>{ve.diem_don ?? '—'}</dd>
            <dt className="text-slate-500">Điểm trả</dt>
            <dd>{ve.diem_tra ?? '—'}</dd>
            <dt className="text-slate-500">Giá vé</dt>
            <dd>{formatCurrency(ve.gia_ve)}</dd>
            <dt className="text-slate-500">Trạng thái</dt>
            <dd className="font-medium text-amber-700">{formatPaymentStatus(ve.trang_thai_thanh_toan)}</dd>
          </dl>
        </li>
      ))}
    </ul>
  )
}
