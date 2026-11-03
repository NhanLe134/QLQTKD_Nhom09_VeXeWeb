import type { Seat, SeatStatus } from '../services/tripService'

type Props = {
  seats: Seat[]
  /** ghe_id đang chọn */
  selected: string[]
  onToggle: (gheId: string) => void
  disabled?: boolean
}

const STATUS_LABEL: Record<SeatStatus, string> = {
  TRONG: 'trống',
  GIU_CHO: 'đang giữ',
  DA_BAN: 'đã bán',
}

const STATUS_CLASS: Record<SeatStatus, string> = {
  TRONG: 'border-slate-300 bg-white text-slate-800 hover:border-blue-500',
  GIU_CHO: 'border-amber-300 bg-amber-100 text-amber-800',
  DA_BAN: 'border-slate-300 bg-slate-300 text-slate-500',
}

const SELECTED_CLASS = 'border-blue-700 bg-blue-700 text-white'

const LEGEND = [
  { label: 'Trống', className: STATUS_CLASS.TRONG },
  { label: 'Đang chọn', className: SELECTED_CLASS },
  { label: 'Đang giữ', className: STATUS_CLASS.GIU_CHO },
  { label: 'Đã bán', className: STATUS_CLASS.DA_BAN },
]

// Trạng thái ghế lấy nguyên từ backend; CSDL không có hàng/cột nên xếp lưới theo mã ghế
export default function SeatMap({ seats, selected, onToggle, disabled = false }: Props) {
  return (
    <div className="space-y-3">
      <ul aria-label="Chú thích sơ đồ ghế" className="flex flex-wrap gap-3 text-sm text-slate-600">
        {LEGEND.map((item) => (
          <li key={item.label} className="flex items-center gap-1">
            <span aria-hidden="true" className={`inline-block h-4 w-4 rounded border ${item.className}`} />
            {item.label}
          </li>
        ))}
      </ul>
      <div role="group" aria-label="Sơ đồ ghế" className="grid max-w-xs grid-cols-4 gap-2">
        {seats.map((seat) => {
          const isSelected = selected.includes(seat.ghe_id)
          const status = isSelected ? 'đang chọn' : STATUS_LABEL[seat.trang_thai]
          return (
            <button
              key={seat.ghe_id}
              type="button"
              aria-label={`Ghế ${seat.so_ghe} (${status})`}
              aria-pressed={isSelected}
              disabled={disabled || seat.trang_thai !== 'TRONG'}
              onClick={() => onToggle(seat.ghe_id)}
              className={`h-12 rounded-md border text-sm font-medium disabled:cursor-not-allowed ${
                isSelected ? SELECTED_CLASS : STATUS_CLASS[seat.trang_thai]
              }`}
            >
              {seat.so_ghe}
            </button>
          )
        })}
      </div>
    </div>
  )
}
