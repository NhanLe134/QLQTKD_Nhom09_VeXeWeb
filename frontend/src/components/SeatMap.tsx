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

/** D = vô lăng, S = ghế (điền lần lượt theo thứ tự backend trả về), _ = lối đi/cửa */
type Cell = 'D' | 'S' | '_'

// CSDL không lưu hàng/cột của ghế nên chọn khuôn theo số ghế của loại xe
const LAYOUTS: Record<number, Cell[][]> = {
  4: [
    ['D', '_', 'S'],
    ['S', 'S', 'S'],
  ],
  7: [
    ['D', '_', 'S'],
    ['S', 'S', 'S'],
    ['S', 'S', 'S'],
  ],
  16: [
    ['D', '_', 'S', 'S'],
    ['S', 'S', '_', '_'],
    ['S', 'S', 'S', 'S'],
    ['S', 'S', 'S', 'S'],
    ['S', 'S', 'S', 'S'],
  ],
}

const GRID_COLS: Record<number, string> = { 3: 'grid-cols-3', 4: 'grid-cols-4' }

/** Khuôn mặc định cho loại xe chưa có sơ đồ riêng: vô lăng một hàng, ghế xếp 4 cột */
function fallbackLayout(count: number): Cell[][] {
  const rows: Cell[][] = [['D', '_', '_', '_']]
  for (let i = 0; i < count; i += 4) {
    rows.push(Array.from({ length: 4 }, (_, j) => (i + j < count ? 'S' : '_')))
  }
  return rows
}

// Trạng thái ghế lấy nguyên từ backend; frontend chỉ quyết định vị trí hiển thị
export default function SeatMap({ seats, selected, onToggle, disabled = false }: Props) {
  const layout = LAYOUTS[seats.length] ?? fallbackLayout(seats.length)
  const columns = layout[0].length
  let nextSeat = 0

  return (
    <div className="grid gap-4 md:grid-cols-[1fr_200px]">
      <div className="rounded-2xl bg-white p-4 shadow-md ring-1 ring-brand-100">
        <div role="group" aria-label="Sơ đồ ghế" className="mx-auto flex max-w-xs flex-col gap-3">
          {layout.map((row, rowIndex) => (
            <div key={rowIndex} data-testid="seat-row" className={`grid gap-x-2 ${GRID_COLS[columns]}`}>
              {row.map((cell, colIndex) => {
                const key = `${rowIndex}-${colIndex}`
                if (cell === 'D') {
                  return (
                    <div key={key} aria-hidden="true" data-testid="steering-wheel" className="flex items-center justify-center">
                      <SteeringWheelIcon className="h-9 w-9 text-slate-700" />
                    </div>
                  )
                }
                const seat = cell === 'S' ? seats[nextSeat++] : undefined
                if (!seat) return <div key={key} aria-hidden="true" />

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
          ))}
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
