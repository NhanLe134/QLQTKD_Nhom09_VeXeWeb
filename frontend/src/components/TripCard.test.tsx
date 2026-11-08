import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { describe, expect, it } from 'vitest'

import type { Trip } from '../services/tripService'
import TripCard from './TripCard'

const TRIP: Trip = {
  chuyen_xe_id: 'CX00000001',
  ten_tuyen: 'Đà Nẵng - Huế',
  diem_di: 'Đà Nẵng',
  diem_den: 'Huế',
  diem_trung_gian: 'Lăng Cô',
  ngay_khoi_hanh: '2026-12-15',
  gio_di: '2026-12-14T23:00:00Z',
  gio_den: '2026-12-15T01:30:00Z',
  ten_loai_xe: 'Xe 4 chỗ',
  so_cho: 4,
  gia_ve: 200000,
  so_ghe_trong: 3,
}

function renderCard(trip: Trip) {
  render(
    <MemoryRouter>
      <TripCard trip={trip} />
    </MemoryRouter>,
  )
}

describe('TripCard', () => {
  it('hiển thị giờ đi → giờ đến (giờ Việt Nam), tuyến, loại xe, giá, số ghế trống', () => {
    renderCard(TRIP)

    expect(screen.getByText('06:00')).toBeInTheDocument()
    expect(screen.getByText('08:30')).toBeInTheDocument()
    expect(screen.getByText('Đà Nẵng - Huế')).toBeInTheDocument()
    expect(screen.getByText('Qua: Lăng Cô')).toBeInTheDocument()
    expect(screen.getByText('Xe 4 chỗ')).toBeInTheDocument()
    expect(screen.getByText('200.000 đ')).toBeInTheDocument()
    expect(screen.getByText('Còn 3 ghế trống')).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'Chọn chuyến' })).toHaveAttribute('href', '/chuyen/CX00000001')
  })

  it('hết ghế thì khóa nút chọn chuyến', () => {
    renderCard({ ...TRIP, so_ghe_trong: 0 })

    expect(screen.getByText('Hết ghế')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Chọn chuyến' })).toBeDisabled()
    expect(screen.queryByRole('link', { name: 'Chọn chuyến' })).not.toBeInTheDocument()
  })

  it('thiếu tên loại xe thì hiện theo số chỗ; thiếu giờ đến, điểm trung gian vẫn hiển thị được', () => {
    renderCard({ ...TRIP, ten_loai_xe: null, so_cho: 16, gio_den: null, diem_trung_gian: null })

    expect(screen.getByText('Xe 16 chỗ')).toBeInTheDocument()
    expect(screen.getByText('06:00')).toBeInTheDocument()
    expect(screen.getByText('--:--')).toBeInTheDocument()
    expect(screen.queryByText(/^Qua:/)).not.toBeInTheDocument()
  })
})
