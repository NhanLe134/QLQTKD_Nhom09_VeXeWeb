import { Link } from 'react-router-dom'

/** TU_HUY, HET_GIO: lý do biết ngay trên trang; HET_HAN, DA_HUY: trạng thái backend trả về. */
export type FailureReason = 'TU_HUY' | 'HET_GIO' | 'HET_HAN' | 'DA_HUY'

// BR-BUS-34: thông báo kèm lý do
const REASONS: Record<FailureReason, string> = {
  TU_HUY: 'Bạn đã hủy đặt vé',
  HET_GIO: 'Hết thời gian giữ chỗ',
  HET_HAN: 'Hết thời gian giữ chỗ',
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
      <div className="flex flex-col gap-1 sm:flex-row sm:items-center sm:justify-between">
        <h1 className="text-xl sm:text-2xl font-bold tracking-tight text-slate-900">Đặt vé thất bại</h1>
        <p className="text-xs font-semibold text-slate-500">
          Mã đơn: <span className="font-mono font-bold text-slate-900">{maDon}</span>
        </p>
      </div>

      <p role="alert" className="rounded-xl bg-rose-50 p-3.5 text-xs sm:text-sm font-semibold text-rose-700 ring-1 ring-rose-200/70">
        {REASONS[reason]}
      </p>

      <div className="flex flex-wrap items-center gap-2 pt-1">
        <Link
          to={`/chuyen/${encodeURIComponent(chuyenXeId)}`}
          className="rounded-lg bg-brand-600 px-4 py-2 text-center text-xs font-bold text-white shadow-2xs transition-all hover:bg-brand-700 active:scale-[0.98]"
        >
          Chọn lại ghế
        </Link>
        <Link
          to="/tim-chuyen"
          className="rounded-lg border border-slate-300 bg-white px-4 py-2 text-center text-xs font-semibold text-slate-700 hover:bg-slate-50 transition-colors"
        >
          Tìm chuyến khác
        </Link>
      </div>
    </section>
  )
}
