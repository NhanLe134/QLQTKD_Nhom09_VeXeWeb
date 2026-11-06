import type { Seat, SeatStatus } from '../services/tripService'
import { SeatIcon, SteeringWheelIcon } from './icons'

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

// Màu icon ghế; trạng thái còn được đọc qua aria-label, không chỉ dựa vào màu
const STATUS_CLASS: Record<SeatStatus, string> = {
  TRONG: 'text-slate-300 hover:text-brand-300',
  GIU_CHO: 'text-violet-400',
  DA_BAN: 'text-brand-500',
}

const SELECTED_CLASS = 'text-amber-400'

const LEGEND = [
  { label: 'Trống', className: STATUS_CLASS.TRONG },
  { label: 'Đang chọn', className: SELECTED_CLASS },
  { label: 'Đang giữ', className: STATUS_CLASS.GIU_CHO },
  { label: 'Đã bán', className: STATUS_CLASS.DA_BAN },
]

// Trạng thái ghế lấy nguyên từ backend; CSDL không có hàng/cột nên xếp lưới theo mã ghế
export default function SeatMap({ seats, selected, onToggle, disabled = false }: Props) {
  return (
    <div className="grid gap-4 md:grid-cols-[1fr_200px]">
      <div className="rounded-2xl bg-white p-4 shadow-md ring-1 ring-brand-100">
        {/* Đầu xe: chỉ để định hướng, không phải ghế */}
        <div aria-hidden="true" className="mb-3 flex items-center justify-between border-b border-dashed border-slate-200 pb-2 text-xs text-slate-500">
          <span>Đầu xe</span>
          <SteeringWheelIcon className="h-8 w-8 text-slate-700" />
        </div>
        <div role="group" aria-label="Sơ đồ ghế" className="mx-auto grid max-w-sm grid-cols-4 gap-x-2 gap-y-3">
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
                className={`flex flex-col items-center rounded-lg py-1 text-xs font-semibold text-slate-700 outline-none focus-visible:ring-2 focus-visible:ring-brand-400 disabled:cursor-not-allowed ${
                  isSelected ? 'bg-amber-50' : ''
                }`}
              >
                <SeatIcon className={`h-9 w-9 ${isSelected ? SELECTED_CLASS : STATUS_CLASS[seat.trang_thai]}`} />
                {seat.so_ghe}
              </button>
            )
          })}
        </div>
      </div>
      <ul
        aria-label="Chú thích sơ đồ ghế"
        className="flex flex-wrap gap-3 self-start rounded-2xl bg-white p-4 text-sm text-slate-600 shadow-md ring-1 ring-brand-100 md:flex-col"
      >
        {LEGEND.map((item) => (
          <li key={item.label} className="flex items-center gap-2">
            <SeatIcon className={`h-5 w-5 ${item.className}`} />
            {item.label}
          </li>
        ))}
      </ul>
    </div>
  )
}
