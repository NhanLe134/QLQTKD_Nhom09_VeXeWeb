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
    <section aria-label="Chọn phương thức thanh toán" className="space-y-3 rounded-2xl border border-slate-200/90 bg-white p-4 shadow-2xs">
      <h2 className="text-sm font-bold text-slate-900">Chọn phương thức thanh toán</h2>
      <div className="flex items-center justify-between border-b border-slate-100 pb-2.5 text-xs font-semibold">
        <span className="text-slate-500">Số tiền cần trả</span>
        <span data-testid="tong-tien-thanh-toan" className="text-base font-black text-amber-600">
          {formatCurrency(tongTien)}
        </span>
      </div>
      <div className="grid gap-2.5 sm:grid-cols-2">
        <button
          type="button"
          onClick={onChooseCash}
          className="rounded-xl border border-slate-200/90 bg-white p-3 text-left transition-all hover:border-brand-400 hover:bg-brand-50/40"
        >
          <span className="block text-xs font-bold text-slate-900">Tiền mặt khi lên xe</span>
          <span className="block text-[11px] text-slate-500 mt-0.5">Trả cho tài xế lúc lên xe</span>
        </button>
        <button
          type="button"
          onClick={onChooseTransfer}
          aria-pressed={transferActive}
          disabled={transferLoading}
          className={`rounded-xl border p-3 text-left transition-all ${
            transferActive
              ? 'border-brand-600 bg-brand-50/70 shadow-2xs ring-1 ring-brand-200'
              : 'border-slate-200/90 bg-white hover:border-brand-400 hover:bg-brand-50/40'
          }`}
        >
          <span className="block text-xs font-bold text-slate-900">Chuyển khoản SePay</span>
          <span className="block text-[11px] text-slate-500 mt-0.5">
            {transferLoading ? 'Đang tạo mã QR…' : 'Quét mã QR để thanh toán'}
          </span>
        </button>
      </div>
      {children && <div className="pt-2">{children}</div>}
      <div className="pt-1">
        <button type="button" onClick={onBack} className="text-xs font-semibold text-slate-500 hover:text-brand-700 underline">
          Quay lại thông tin hành khách
        </button>
      </div>
    </section>
  )
}
