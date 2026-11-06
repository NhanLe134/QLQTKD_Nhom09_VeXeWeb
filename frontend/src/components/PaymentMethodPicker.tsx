import type { ReactNode } from 'react'

import { formatCurrency } from '../utils/format'

type Props = {
  /** Tổng tiền do backend tính */
  tongTien: number
  onChooseCash: () => void
  /** Bấm "Chuyển khoản SePay": hiện/đổi QR ngay dưới hai ô (BR-BUS-27) */
  onChooseTransfer: () => void
  /** Đang chọn chuyển khoản (ô được tô đậm, QR đang hiển thị) */
  transferActive: boolean
  /** Chờ backend trả QR */
  transferLoading?: boolean
  onBack: () => void
  /** Panel QR hiển thị phía dưới, chính giữa hai ô phương thức */
  children?: ReactNode
}

/** Chọn phương thức thanh toán (BR-BUS-27): tiền mặt hoặc chuyển khoản SePay. */
export default function PaymentMethodPicker({
  tongTien,
  onChooseCash,
  onChooseTransfer,
  transferActive,
  transferLoading = false,
  onBack,
  children,
}: Props) {
  return (
    <section aria-label="Chọn phương thức thanh toán" className="space-y-3 rounded-xl border border-brand-100 bg-white shadow-sm p-4">
      <h2 className="text-lg font-semibold">Chọn phương thức thanh toán</h2>
      <p className="flex justify-between font-semibold">
        <span>Số tiền cần trả</span>
        <span data-testid="tong-tien-thanh-toan">{formatCurrency(tongTien)}</span>
      </p>
      <div className="grid gap-2 sm:grid-cols-2">
        <button
          type="button"
          onClick={onChooseCash}
          className="rounded-lg border border-brand-300 px-4 py-3 text-left hover:bg-brand-50"
        >
          <span className="block font-medium text-brand-800">Tiền mặt khi lên xe</span>
          <span className="block text-sm text-slate-600">Trả cho tài xế lúc lên xe</span>
        </button>
        <button
          type="button"
          onClick={onChooseTransfer}
          aria-pressed={transferActive}
          disabled={transferLoading}
          className={`rounded-lg border px-4 py-3 text-left hover:bg-brand-50 ${
            transferActive ? 'border-brand-600 bg-brand-100' : 'border-brand-300'
          }`}
        >
          <span className="block font-medium text-brand-800">Chuyển khoản SePay</span>
          <span className="block text-sm text-slate-600">
            {transferLoading ? 'Đang tạo mã QR…' : 'Quét mã QR để thanh toán'}
          </span>
        </button>
      </div>
      {children && <div className="pt-2">{children}</div>}
      <button type="button" onClick={onBack} className="text-sm font-medium text-slate-700 underline">
        Quay lại thông tin hành khách
      </button>
    </section>
  )
}
