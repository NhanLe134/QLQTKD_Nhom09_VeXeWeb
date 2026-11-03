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

  it('khóa mọi ghế khi disabled', () => {
    render(<SeatMap seats={SEATS} selected={[]} onToggle={vi.fn()} disabled />)

    expect(screen.getByRole('button', { name: 'Ghế A01 (trống)' })).toBeDisabled()
  })
})
