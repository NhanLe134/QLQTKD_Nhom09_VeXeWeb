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
      className="mx-auto w-full max-w-sm space-y-3 rounded-lg border border-blue-200 bg-blue-50 p-4 text-center"
    >
      <h3 className="font-semibold text-blue-900">Quét mã QR để chuyển khoản</h3>
      <img
        src={qr.qr_url}
        alt={`Mã QR chuyển khoản ${formatCurrency(qr.so_tien)}`}
        data-testid="qr-se-pay-hinh"
        className="mx-auto h-48 w-48 rounded-md bg-white p-1"
      />
      <dl className="space-y-1 text-sm">
        <div className="flex justify-between">
          <dt className="text-slate-600">Số tiền</dt>
          <dd data-testid="qr-se-pay-so-tien" className="font-semibold">
            {formatCurrency(qr.so_tien)}
          </dd>
        </div>
        <div className="flex justify-between gap-2">
          <dt className="text-slate-600">Nội dung chuyển khoản</dt>
          <dd data-testid="qr-se-pay-noi-dung" className="font-mono font-semibold">
            {qr.noi_dung}
          </dd>
        </div>
      </dl>
      <p className="text-xs text-slate-600">
        Vui lòng chuyển đúng số tiền và nội dung trên để vé được xác nhận tự động.
      </p>
      {expired ? (
        <p role="alert" className="rounded-md bg-red-50 px-3 py-2 text-sm font-medium text-red-700">
          Quá thời gian chuyển khoản. Bấm "Chuyển khoản SePay" để nhận lại mã QR.
        </p>
      ) : (
        <p className="text-slate-700">
          Thời gian chuyển khoản còn lại:{' '}
          <span
            role="timer"
            aria-label="Thời gian chuyển khoản còn lại"
            className="font-mono text-lg font-semibold text-blue-700"
          >
            {conLaiMs === null ? formatCountdown(0) : formatCountdown(conLaiMs)}
          </span>
        </p>
      )}
    </section>
  )
}
