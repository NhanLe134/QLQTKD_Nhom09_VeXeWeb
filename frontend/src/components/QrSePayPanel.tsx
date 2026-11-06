import { formatCountdown, formatCurrency } from '../utils/format'
import type { QrSePay } from '../services/bookingService'

type Props = {
  qr: QrSePay
  /** Số ms còn lại của cửa sổ chuyển khoản (useCountdown); null là chưa bắt đầu */
  conLaiMs: number | null
}

/**
 * Mã QR chuyển khoản SePay (BR-BUS-29): ảnh QR, số tiền và nội dung khách phải
 * giữ nguyên khi chuyển. Hết cửa sổ hiển thị thì báo khách bấm lại để nhận QR.
 */
export default function QrSePayPanel({ qr, conLaiMs }: Props) {
  const expired = conLaiMs !== null && conLaiMs <= 0
  return (
    <section
      aria-label="Mã QR chuyển khoản SePay"
      data-testid="qr-se-pay-panel"
      className="mx-auto w-full max-w-xs space-y-2.5 rounded-2xl border border-brand-200/90 bg-brand-50/50 p-4 text-center shadow-2xs"
    >
      <h3 className="text-xs font-bold uppercase tracking-wider text-brand-900">Quét mã QR để chuyển khoản</h3>
      <div className="flex justify-center py-1">
        <img
          src={qr.qr_url}
          alt={`Mã QR chuyển khoản ${formatCurrency(qr.so_tien)}`}
          data-testid="qr-se-pay-hinh"
          className="h-40 w-40 rounded-xl bg-white p-2 shadow-2xs border border-brand-100 object-contain"
        />
      </div>
      <dl className="space-y-1.5 rounded-xl bg-white p-2.5 text-xs border border-brand-100/80">
        <div className="flex items-center justify-between">
          <dt className="text-slate-500 font-medium">Số tiền</dt>
          <dd data-testid="qr-se-pay-so-tien" className="font-extrabold text-amber-600">
            {formatCurrency(qr.so_tien)}
          </dd>
        </div>
        <div className="flex items-center justify-between gap-2 border-t border-slate-100 pt-1">
          <dt className="text-slate-500 font-medium">Nội dung chuyển khoản</dt>
          <dd data-testid="qr-se-pay-noi-dung" className="font-mono font-bold text-brand-800 bg-brand-50 px-1.5 py-0.5 rounded">
            {qr.noi_dung}
          </dd>
        </div>
      </dl>
      <p className="text-[11px] text-slate-500">
        Vui lòng chuyển đúng số tiền và nội dung trên để vé được xác nhận tự động.
      </p>
      <p role="status" className="flex items-center justify-center gap-1.5 text-xs font-semibold text-brand-700">
        <span
          aria-hidden="true"
          className="h-3.5 w-3.5 animate-spin rounded-full border-2 border-brand-300 border-t-brand-700"
        />
        Đang chờ xác nhận thanh toán…
      </p>
      {expired ? (
        <p role="alert" className="rounded-lg bg-rose-50 px-2.5 py-1.5 text-xs font-semibold text-rose-700 ring-1 ring-rose-200/60">
          Quá thời gian chuyển khoản. Bấm "Chuyển khoản SePay" để nhận lại mã QR.
        </p>
      ) : (
        <p className="text-xs text-slate-600 font-medium">
          Thời gian chuyển khoản còn lại:{' '}
          <span
            role="timer"
            aria-label="Thời gian chuyển khoản còn lại"
            className="font-mono text-sm font-bold text-brand-700"
          >
            {conLaiMs === null ? formatCountdown(0) : formatCountdown(conLaiMs)}
          </span>
        </p>
      )}
    </section>
  )
}
