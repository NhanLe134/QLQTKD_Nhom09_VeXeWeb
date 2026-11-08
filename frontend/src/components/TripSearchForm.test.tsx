import { fireEvent, render, screen } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import type { TripSearchQuery } from '../services/tripService'
import TripSearchForm from './TripSearchForm'

const LOCATIONS = {
  diem_di: ['Đà Nẵng', 'Hội An', 'Huế'],
  diem_den: ['Đà Nẵng', 'Hội An', 'Huế'],
}
const EMPTY: TripSearchQuery = { diemDi: '', diemDen: '', ngay: '' }

function renderForm(initialValues: TripSearchQuery = EMPTY, locations = LOCATIONS) {
  const onSearch = vi.fn()
  render(<TripSearchForm locations={locations} initialValues={initialValues} onSearch={onSearch} />)
  return onSearch
}

function fill(diemDi: string, diemDen: string, ngay: string) {
  fireEvent.change(screen.getByLabelText('Điểm đi'), { target: { value: diemDi } })
  fireEvent.change(screen.getByLabelText('Điểm đến'), { target: { value: diemDen } })
  fireEvent.change(screen.getByLabelText('Ngày đi'), { target: { value: ngay } })
  fireEvent.click(screen.getByRole('button', { name: 'Tìm chuyến' }))
}

beforeEach(() => {
  // 01/12/2026 10:00 giờ Việt Nam
  vi.useFakeTimers({ toFake: ['Date'] })
  vi.setSystemTime(new Date('2026-12-01T03:00:00Z'))
})

afterEach(() => {
  vi.useRealTimers()
})

describe('TripSearchForm', () => {
  it('ô chọn có các điểm lấy từ backend', () => {
    renderForm()

    const options = screen.getAllByRole('option').map((option) => option.textContent)
    expect(options).toEqual([
      'Chọn điểm đi',
      'Đà Nẵng',
      'Hội An',
      'Huế',
      'Chọn điểm đến',
      'Đà Nẵng',
      'Hội An',
      'Huế',
    ])
  })

  it('không cho chọn ngày trước hôm nay (giờ Việt Nam)', () => {
    renderForm()

    expect(screen.getByLabelText('Ngày đi')).toHaveAttribute('min', '2026-12-01')
  })

  it('gửi tiêu chí hợp lệ', () => {
    const onSearch = renderForm()

    fill('Đà Nẵng', 'Huế', '2026-12-15')

    expect(onSearch).toHaveBeenCalledWith({ diemDi: 'Đà Nẵng', diemDen: 'Huế', ngay: '2026-12-15' })
  })

  it('cho phép tìm ngày hôm nay', () => {
    const onSearch = renderForm()

    fill('Đà Nẵng', 'Huế', '2026-12-01')

    expect(onSearch).toHaveBeenCalledOnce()
  })

  it('báo lỗi khi chưa chọn đủ', () => {
    const onSearch = renderForm()

    fireEvent.click(screen.getByRole('button', { name: 'Tìm chuyến' }))

    expect(screen.getByText('Vui lòng chọn điểm đi')).toBeInTheDocument()
    expect(screen.getByText('Vui lòng chọn điểm đến')).toBeInTheDocument()
    expect(screen.getByText('Vui lòng chọn ngày đi')).toBeInTheDocument()
    expect(onSearch).not.toHaveBeenCalled()
  })

  it('không cho điểm đi trùng điểm đến', () => {
    const onSearch = renderForm()

    fill('Huế', 'Huế', '2026-12-15')

    expect(screen.getByLabelText('Điểm đến')).toHaveAttribute('aria-invalid', 'true')
    expect(screen.getByText('Điểm đến phải khác điểm đi')).toBeInTheDocument()
    expect(onSearch).not.toHaveBeenCalled()
  })

  it('không cho tìm ngày trong quá khứ', () => {
    const onSearch = renderForm()

    fill('Đà Nẵng', 'Huế', '2026-11-30')

    expect(screen.getByText('Không chọn được ngày trong quá khứ')).toBeInTheDocument()
    expect(onSearch).not.toHaveBeenCalled()
  })

  it('điền sẵn giá trị ban đầu (từ URL)', () => {
    renderForm({ diemDi: 'Hội An', diemDen: 'Huế', ngay: '2026-12-16' })

    expect(screen.getByLabelText('Điểm đi')).toHaveValue('Hội An')
    expect(screen.getByLabelText('Điểm đến')).toHaveValue('Huế')
    expect(screen.getByLabelText('Ngày đi')).toHaveValue('2026-12-16')
  })

  it('khóa ô chọn và nút khi đang tải danh sách điểm', () => {
    render(<TripSearchForm locations={null} initialValues={EMPTY} onSearch={vi.fn()} />)

    expect(screen.getByLabelText('Điểm đi')).toBeDisabled()
    expect(screen.getByLabelText('Điểm đến')).toBeDisabled()
    expect(screen.getByRole('button', { name: 'Tìm chuyến' })).toBeDisabled()
  })
})
