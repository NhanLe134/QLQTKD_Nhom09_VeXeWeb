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

const STATUS_CLASS: Record<SeatStatus, string> = {
  TRONG: 'text-slate-400 group-hover:text-brand-600',
  GIU_CHO: 'text-purple-400',
  DA_BAN: 'text-slate-300',
}

const SELECTED_CLASS = 'text-amber-950'

const LEGEND = [
  { label: 'Trống', className: 'text-slate-400 bg-white border border-slate-200' },
  { label: 'Đang chọn', className: 'text-amber-950 bg-amber-400 border border-amber-500' },
  { label: 'Đang giữ', className: 'text-purple-500 bg-purple-50 border border-purple-200' },
  { label: 'Đã bán', className: 'text-slate-400 bg-slate-100 border border-slate-200' },
]

/** D = vô lăng, S = ghế (điền lần lượt theo thứ tự backend trả về), _ = lối đi/cửa */
type Cell = 'D' | 'S' | '_'

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

function fallbackLayout(count: number): Cell[][] {
  const rows: Cell[][] = [['D', '_', '_', '_']]
  for (let i = 0; i < count; i += 4) {
    rows.push(Array.from({ length: 4 }, (_, j) => (i + j < count ? 'S' : '_')))
  }
  return rows
}

export default function SeatMap({ seats, selected, onToggle, disabled = false }: Props) {
  const layout = LAYOUTS[seats.length] ?? fallbackLayout(seats.length)
  const columns = layout[0].length
  let nextSeat = 0

  return (
    <div className="grid gap-6 md:grid-cols-[1fr_220px] items-start">
      {/* Khoang xe mô phỏng */}
      <div className="rounded-3xl border border-slate-200/90 bg-white p-6 shadow-xs">
        <div className="mb-4 text-center">
          <span className="inline-block rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-500">
            Đầu xe
          </span>
        </div>

        <div
          role="group"
          aria-label="Sơ đồ ghế"
          className="mx-auto flex max-w-xs flex-col gap-3 rounded-2xl border-2 border-dashed border-slate-200 bg-slate-50/70 p-5"
        >
          {layout.map((row, rowIndex) => (
            <div key={rowIndex} data-testid="seat-row" className={`grid gap-2.5 ${GRID_COLS[columns]}`}>
              {row.map((cell, colIndex) => {
                const key = `${rowIndex}-${colIndex}`
                if (cell === 'D') {
                  return (
                    <div
                      key={key}
                      aria-hidden="true"
                      data-testid="steering-wheel"
                      className="flex h-14 items-center justify-center rounded-xl bg-slate-200/70 text-slate-600"
                    >
                      <SteeringWheelIcon className="h-7 w-7" />
                    </div>
                  )
                }
                const seat = cell === 'S' ? seats[nextSeat++] : undefined
                if (!seat) return <div key={key} aria-hidden="true" className="h-14" />

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
                    className={`group flex h-14 flex-col items-center justify-center rounded-xl border text-xs font-bold transition-all duration-150 outline-none focus-visible:ring-2 focus-visible:ring-brand-400 disabled:cursor-not-allowed ${
                      isSelected
                        ? 'border-amber-500 bg-amber-400 text-slate-950 shadow-xs scale-105'
                        : seat.trang_thai === 'TRONG'
                          ? 'border-slate-200 bg-white text-slate-700 hover:border-brand-400 hover:bg-brand-50/60 hover:text-brand-700 shadow-2xs'
                          : seat.trang_thai === 'GIU_CHO'
                            ? 'border-purple-200 bg-purple-50/60 text-purple-400 opacity-80'
                            : 'border-slate-200 bg-slate-100 text-slate-400 opacity-70'
                    }`}
                  >
                    <SeatIcon
                      className={`h-6 w-6 transition-transform group-hover:scale-110 ${
                        isSelected ? SELECTED_CLASS : STATUS_CLASS[seat.trang_thai]
                      }`}
                    />
                    <span>{seat.so_ghe}</span>
                  </button>
                )
              })}
            </div>
          ))}
        </div>

        <div className="mt-4 text-center">
          <span className="inline-block rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-500">
            Đuôi xe
          </span>
        </div>
      </div>

      {/* Bảng chú thích trạng thái ghế */}
      <ul
        aria-label="Chú thích sơ đồ ghế"
        className="flex flex-wrap gap-2.5 rounded-3xl border border-slate-200/90 bg-white p-5 text-xs font-semibold text-slate-600 shadow-xs md:flex-col"
      >
        <li className="w-full pb-1 border-b border-slate-100 text-slate-900 font-bold uppercase tracking-wider text-[11px]">
          Chú thích ghế
        </li>
        {LEGEND.map((item) => (
          <li key={item.label} className="flex items-center gap-2.5 py-1">
            <span className={`flex h-6 w-6 items-center justify-center rounded-lg p-1 ${item.className}`}>
              <SeatIcon className="h-4 w-4" />
            </span>
            <span>{item.label}</span>
          </li>
        ))}
      </ul>
    </div>
  )
}
