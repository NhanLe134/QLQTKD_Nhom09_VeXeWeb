import { Link } from 'react-router-dom'

import type { CancelReceipt as Receipt } from '../services/bookingService'
import { formatCurrency, formatDate, formatDateTime, formatRefundStatus, formatTime } from '../utils/format'

type Props = {
  receipt: Receipt
  /** Quay lại danh sách vé; không truyền khi đơn không còn vé nào */
  onDone?: () => void
}

/** Màn hình "Hủy vé thành công" kèm biên lai; mọi số tiền, trạng thái do backend trả. */
export default function CancelReceipt({ receipt, onDone }: Props) {
  const { chuyen } = receipt
  const waiting = receipt.ve.some((ve) => ve.trang_thai_hoan === 'CHO_HOAN_TIEN')

  return (
    <section className="space-y-4">
      <div className="flex flex-col gap-1 sm:flex-row sm:items-center sm:justify-between">
        <h1 className="text-xl sm:text-2xl font-bold tracking-tight text-slate-900">Hủy vé thành công</h1>
        <p className="text-xs font-semibold text-slate-500">
          Mã đơn: <span className="font-mono font-bold text-slate-900">{receipt.ma_don}</span>
        </p>
      </div>

      <div role="status" className="rounded-xl bg-emerald-50 p-3.5 text-xs sm:text-sm font-semibold text-emerald-800 ring-1 ring-emerald-200/70">
        Vé đã được hủy, ghế đã được mở lại.
        {waiting && ' Nhà xe sẽ chuyển khoản tiền hoàn vào tài khoản bạn đã cung cấp.'}
      </div>

      <div className="rounded-2xl border border-slate-200/90 bg-white p-4 shadow-2xs space-y-1">
        <p className="text-sm font-bold text-slate-900">{chuyen.ten_tuyen}</p>
        <p className="text-xs text-slate-600">
          {formatTime(chuyen.gio_di)} ngày {formatDate(chuyen.ngay_khoi_hanh)}
        </p>
      </div>

      <ul aria-label="Biên lai hủy vé" className="space-y-2.5">
        {receipt.ve.map((ve) => (
          <li
            key={ve.ve_id}
            aria-label={`Vé đã hủy ${ve.ve_id}`}
            className="rounded-xl border border-slate-200/90 bg-white p-3 text-xs shadow-2xs"
          >
            <div className="flex items-center justify-between gap-2 border-b border-slate-100 pb-2">
              <p className="font-bold text-slate-700">
                Mã vé: <span className="font-mono text-brand-800">{ve.ve_id}</span>
              </p>
              <span className="rounded-md bg-slate-100 px-2 py-0.5 font-bold text-slate-700">Ghế {ve.so_ghe}</span>
            </div>
            <dl className="mt-2 grid grid-cols-2 gap-x-3 gap-y-1.5">
              <dt className="text-slate-500">Giá vé</dt>
              <dd className="text-right font-semibold text-slate-800">{formatCurrency(ve.gia_ve)}</dd>
              <dt className="text-slate-500">Số tiền hoàn</dt>
              <dd className="text-right font-bold text-amber-600">{formatCurrency(ve.muc_hoan)}</dd>
              <dt className="text-slate-500">Trạng thái hoàn</dt>
              <dd className={`text-right font-semibold ${ve.trang_thai_hoan === 'KHONG_HOAN_TIEN' ? 'text-slate-600' : 'text-emerald-700'}`}>
                {formatRefundStatus(ve.trang_thai_hoan)}
              </dd>
              <dt className="text-slate-500">Thời điểm hủy</dt>
              <dd className="text-right text-slate-700">{formatDateTime(ve.ngay_huy)}</dd>
            </dl>
          </li>
        ))}
      </ul>

      <div className="space-y-1.5 rounded-2xl border border-slate-200/90 bg-white p-4 text-xs shadow-2xs">
        <div className="flex items-center justify-between font-bold text-slate-800">
          <span>Tổng tiền hoàn</span>
          <span data-testid="tong-hoan" className="text-base font-black text-amber-600">
            {formatCurrency(receipt.tong_hoan)}
          </span>
        </div>
        {receipt.ngan_hang_nhan && (
          <p className="text-slate-600">
            Tài khoản nhận: {receipt.ngan_hang_nhan} {receipt.so_tai_khoan_nhan}
          </p>
        )}
      </div>

      <div className="flex flex-wrap items-center gap-2 pt-1">
        {onDone && (
          <button
            type="button"
            onClick={onDone}
            className="rounded-lg bg-brand-600 px-4 py-2 text-xs font-bold text-white shadow-2xs hover:bg-brand-700"
          >
            Xem vé còn lại
          </button>
        )}
        <Link
          to="/"
          className="rounded-lg border border-slate-300 bg-white px-4 py-2 text-center text-xs font-semibold text-slate-700 hover:bg-slate-50"
        >
          Về trang chủ
        </Link>
      </div>
    </section>
  )
}
