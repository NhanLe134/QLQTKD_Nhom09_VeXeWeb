import { Link } from 'react-router-dom'

/** TU_HUY, HET_GIO: lý do biết ngay trên trang; HET_HAN, DA_HUY: trạng thái backend trả về. */
export type FailureReason = 'TU_HUY' | 'HET_GIO' | 'HET_HAN' | 'DA_HUY'

// BR-BUS-34: thông báo kèm lý do
const REASONS: Record<FailureReason, string> = {
  TU_HUY: 'Bạn đã hủy đặt vé',
  HET_GIO: 'Hết thời gian giữ chỗ',
  HET_HAN: 'Hết thời gian giữ chỗ',
  // Backend không phân biệt đơn tự hủy với đơn hết hạn đã được nhả (docs/API.md)
  DA_HUY: 'Đơn đặt vé đã bị hủy hoặc hết thời gian giữ chỗ',
}

type Props = {
  reason: FailureReason
  maDon: string
  chuyenXeId: string
}

export default function BookingFailed({ reason, maDon, chuyenXeId }: Props) {
  return (
    <section className="space-y-4">
      <h1 className="text-2xl font-bold text-brand-800">Đặt vé thất bại</h1>
      <p role="alert" className="rounded-lg bg-red-50 px-3 py-2 font-medium text-red-700">
        {REASONS[reason]}
      </p>
      <p className="text-slate-600">
        Mã đơn: <span className="font-semibold text-slate-900">{maDon}</span>
      </p>
      <div className="flex flex-col gap-2 sm:flex-row">
        <Link
          to={`/chuyen/${encodeURIComponent(chuyenXeId)}`}
          className="rounded-lg bg-brand-700 px-4 py-2 text-center font-semibold text-white shadow-sm hover:bg-brand-800"
        >
          Chọn lại ghế
        </Link>
        <Link
          to="/tim-chuyen"
          className="rounded-lg border border-slate-300 px-4 py-2 text-center font-medium text-slate-700 hover:bg-slate-50"
        >
          Tìm chuyến khác
        </Link>
      </div>
    </section>
  )
}
