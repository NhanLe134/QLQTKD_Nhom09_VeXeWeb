import type { Ticket } from '../services/bookingService'
import { formatCurrency, formatPaymentStatus } from '../utils/format'

type Props = {
  tickets: Ticket[]
  /** Nhãn của danh sách cho trình đọc màn hình */
  label?: string
  /** Callback khi người dùng bấm Đổi vé */
  onExchange?: (ticket: Ticket) => void
  /** Callback khi người dùng bấm Hủy vé; được hủy hay không do backend quyết định */
  onCancel?: (ticket: Ticket) => void
}

/**
 * Vé điện tử: mỗi ghế một vé, hiển thị gọn gàng, rõ ràng
 */
export default function TicketList({ tickets, label = 'Vé điện tử', onExchange, onCancel }: Props) {
  return (
    <ul aria-label={label} className="space-y-2.5">
      {tickets.map((ve) => (
        <li
          key={ve.ve_id}
          aria-label={`Vé ${ve.ve_id}`}
          className="rounded-xl border border-slate-200/90 bg-white p-3 shadow-2xs transition-all hover:border-brand-200 hover:shadow-xs"
        >
          {/* Hàng tiêu đề vé */}
          <div className="flex items-center justify-between gap-2 border-b border-slate-100 pb-2">
            <p className="text-xs font-bold text-slate-700">
              Mã vé: <span className="font-mono font-bold text-brand-800">{ve.ve_id}</span>
            </p>
            <span className="rounded-md bg-brand-50 px-2 py-0.5 text-xs font-bold text-brand-700 ring-1 ring-brand-200/60">
              Ghế {ve.so_ghe}
            </span>
          </div>

          {/* Chi tiết thông tin vé */}
          <dl className="mt-2 grid grid-cols-2 gap-x-3 gap-y-1.5 text-xs sm:grid-cols-3">
            <div>
              <dt className="text-[11px] font-medium text-slate-400">Hành khách</dt>
              <dd className="font-semibold text-slate-800 truncate">{ve.ho_ten ?? '—'}</dd>
            </div>
            <div>
              <dt className="text-[11px] font-medium text-slate-400">Giá vé</dt>
              <dd className="font-bold text-amber-600">{formatCurrency(ve.gia_ve)}</dd>
            </div>
            <div>
              <dt className="text-[11px] font-medium text-slate-400">Trạng thái</dt>
              <dd className={`font-semibold ${ve.trang_thai_thanh_toan === 'DA_THANH_TOAN' ? 'text-emerald-700' : 'text-amber-700'}`}>
                {formatPaymentStatus(ve.trang_thai_thanh_toan)}
              </dd>
            </div>
            <div className="col-span-2 sm:col-span-3 grid grid-cols-1 sm:grid-cols-2 gap-x-3 gap-y-1 pt-1.5 border-t border-slate-100">
              <div>
                <dt className="text-[11px] font-medium text-slate-400">Điểm đón</dt>
                <dd className="text-slate-600 truncate">{ve.diem_don ?? '—'}</dd>
              </div>
              <div>
                <dt className="text-[11px] font-medium text-slate-400">Điểm trả</dt>
                <dd className="text-slate-600 truncate">{ve.diem_tra ?? '—'}</dd>
              </div>
            </div>
          </dl>

          {/* Nút Đổi vé, Hủy vé */}
          {(onExchange || onCancel) && ve.trang_thai_ve === 'DA_XAC_NHAN' && (
            <div className="mt-2.5 flex justify-end gap-2 border-t border-slate-100 pt-2">
              {onExchange && (
                <button
                  type="button"
                  onClick={() => onExchange(ve)}
                  className="inline-flex items-center gap-1 rounded-lg border border-brand-200 bg-brand-50 px-2.5 py-1 text-xs font-bold text-brand-700 hover:bg-brand-100 transition-colors"
                >
                  <svg className="h-3 w-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M8 7h12m0 0l-4-4m4 4l-4 4m0 6H4m0 0l4 4m-4-4l4-4" />
                  </svg>
                  <span>Đổi vé</span>
                </button>
              )}
              {onCancel && (
                <button
                  type="button"
                  onClick={() => onCancel(ve)}
                  className="inline-flex items-center gap-1 rounded-lg border border-rose-200 bg-rose-50 px-2.5 py-1 text-xs font-bold text-rose-700 hover:bg-rose-100 transition-colors"
                >
                  Hủy vé
                </button>
              )}
            </div>
          )}
        </li>
      ))}
    </ul>
  )
}
