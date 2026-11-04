import { fireEvent, render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'

import type { Seat } from '../services/tripService'
import SeatMap from './SeatMap'

const SEATS: Seat[] = [
  { ghe_id: 'GH1', so_ghe: 'A01', trang_thai: 'TRONG' },
  { ghe_id: 'GH2', so_ghe: 'A02', trang_thai: 'GIU_CHO' },
  { ghe_id: 'GH3', so_ghe: 'A03', trang_thai: 'DA_BAN' },
  { ghe_id: 'GH4', so_ghe: 'A04', trang_thai: 'TRONG' },
]

function makeSeats(count: number): Seat[] {
  return Array.from({ length: count }, (_, i) => {
    const code = `A${String(i + 1).padStart(2, '0')}`
    return { ghe_id: `GH${i + 1}`, so_ghe: code, trang_thai: 'TRONG' }
  })
}

/** Đọc sơ đồ thành bảng: D = vô lăng, _ = ô trống, còn lại là mã ghế */
function readRows(): string[][] {
  return screen.getAllByTestId('seat-row').map((row) =>
    Array.from(row.children).map((cell) => {
      if (cell.getAttribute('data-testid') === 'steering-wheel') return 'D'
      return cell.textContent || '_'
    }),
  )
}

describe('SeatMap', () => {
  it('hiện mọi ghế theo mã ghế, kèm trạng thái và chú thích', () => {
    render(<SeatMap seats={SEATS} selected={['GH4']} onToggle={vi.fn()} />)

    const buttons = screen.getAllByRole('button')
    expect(buttons.map((button) => button.textContent)).toEqual(['A01', 'A02', 'A03', 'A04'])
    expect(screen.getByRole('button', { name: 'Ghế A01 (trống)' })).toBeEnabled()
    expect(screen.getByRole('button', { name: 'Ghế A02 (đang giữ)' })).toBeDisabled()
    expect(screen.getByRole('button', { name: 'Ghế A03 (đã bán)' })).toBeDisabled()
    expect(screen.getByRole('button', { name: 'Ghế A04 (đang chọn)' })).toHaveAttribute('aria-pressed', 'true')

    const legend = screen.getByRole('list', { name: 'Chú thích sơ đồ ghế' })
    expect(legend).toHaveTextContent('Trống')
    expect(legend).toHaveTextContent('Đang chọn')
    expect(legend).toHaveTextContent('Đang giữ')
    expect(legend).toHaveTextContent('Đã bán')
  })

  it('bấm ghế trống gọi onToggle với ghe_id', () => {
    const onToggle = vi.fn()
    render(<SeatMap seats={SEATS} selected={[]} onToggle={onToggle} />)

    fireEvent.click(screen.getByRole('button', { name: 'Ghế A01 (trống)' }))
    fireEvent.click(screen.getByRole('button', { name: 'Ghế A02 (đang giữ)' }))

    expect(onToggle).toHaveBeenCalledTimes(1)
    expect(onToggle).toHaveBeenCalledWith('GH1')
  })

  it.each([
    // [số ghế, ô của từng hàng: D = vô lăng, _ = ô trống, còn lại là mã ghế]
    [4, [['D', '_', 'A01'], ['A02', 'A03', 'A04']]],
    [7, [['D', '_', 'A01'], ['A02', 'A03', 'A04'], ['A05', 'A06', 'A07']]],
    [
      16,
      [
        ['D', '_', 'A01', 'A02'],
        ['A03', 'A04', '_', '_'],
        ['A05', 'A06', 'A07', 'A08'],
        ['A09', 'A10', 'A11', 'A12'],
        ['A13', 'A14', 'A15', 'A16'],
      ],
    ],
  ])('xếp xe %i chỗ đúng sơ đồ', (count, expected) => {
    render(<SeatMap seats={makeSeats(count)} selected={[]} onToggle={vi.fn()} />)

    expect(readRows()).toEqual(expected)
    expect(screen.getByTestId('steering-wheel')).toHaveAttribute('aria-hidden', 'true')
  })

  it('loại xe chưa có sơ đồ riêng thì xếp 4 cột sau hàng vô lăng', () => {
    render(<SeatMap seats={makeSeats(6)} selected={[]} onToggle={vi.fn()} />)

    expect(readRows()).toEqual([
      ['D', '_', '_', '_'],
      ['A01', 'A02', 'A03', 'A04'],
      ['A05', 'A06', '_', '_'],
    ])
  })

  it('khóa mọi ghế khi disabled', () => {
    render(<SeatMap seats={SEATS} selected={[]} onToggle={vi.fn()} disabled />)

    expect(screen.getByRole('button', { name: 'Ghế A01 (trống)' })).toBeDisabled()
  })
})
