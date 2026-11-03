import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { describe, expect, it } from 'vitest'

import BookingFailed, { type FailureReason } from './BookingFailed'

function renderFailed(reason: FailureReason) {
  render(
    <MemoryRouter>
      <BookingFailed reason={reason} maDon="DH00100000" chuyenXeId="CX00000001" />
    </MemoryRouter>,
  )
}

describe('BookingFailed', () => {
  it.each<[FailureReason, string]>([
    ['TU_HUY', 'Bạn đã hủy đặt vé'],
    ['HET_GIO', 'Hết thời gian giữ chỗ'],
    ['HET_HAN', 'Hết thời gian giữ chỗ'],
    ['DA_HUY', 'Đơn đặt vé đã bị hủy hoặc hết thời gian giữ chỗ'],
  ])('lý do %s: "%s" (BR-BUS-34)', (reason, message) => {
    renderFailed(reason)

    expect(screen.getByRole('heading', { name: 'Đặt vé thất bại' })).toBeInTheDocument()
    expect(screen.getByRole('alert')).toHaveTextContent(message)
    expect(screen.getByText('DH00100000')).toBeInTheDocument()
  })

  it('cho chọn lại ghế của chuyến cũ hoặc tìm chuyến khác', () => {
    renderFailed('TU_HUY')

    expect(screen.getByRole('link', { name: 'Chọn lại ghế' })).toHaveAttribute('href', '/chuyen/CX00000001')
    expect(screen.getByRole('link', { name: 'Tìm chuyến khác' })).toHaveAttribute('href', '/tim-chuyen')
  })
})
