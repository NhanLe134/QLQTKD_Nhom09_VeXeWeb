import { formatCurrency } from '../utils/format'

type Props = {
  /** Tổng tiền do backend tính */
  tongTien: number
  onChooseCash: () => void
  onBack: () => void
}

/** Chọn phương thức thanh toán (BR-BUS-27). Chuyển khoản SePay làm ở task #11. */
export default function PaymentMethodPicker({ tongTien, onChooseCash, onBack }: Props) {
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
          disabled
          className="rounded-lg border border-slate-200 px-4 py-3 text-left disabled:cursor-not-allowed disabled:bg-slate-50"
        >
          <span className="block font-medium text-slate-500">Chuyển khoản SePay</span>
          <span className="block text-sm text-slate-500">Sắp có</span>
        </button>
      </div>
      <button type="button" onClick={onBack} className="text-sm font-medium text-slate-700 underline">
        Quay lại thông tin hành khách
      </button>
    </section>
  )
}
