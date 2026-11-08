import { fireEvent, render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'

import { HELD_BOOKING, SAVED_BOOKING } from '../utils/testBookings'
import BookingDetailsSummary from './BookingDetailsSummary'

describe('BookingDetailsSummary', () => {
  it('khóa "Tiếp tục thanh toán" khi backend báo chưa nhập đủ thông tin', () => {
    const onContinue = vi.fn()
    render(<BookingDetailsSummary booking={HELD_BOOKING} onEdit={vi.fn()} onContinue={onContinue} />)

    const button = screen.getByRole('button', { name: 'Tiếp tục thanh toán' })
    expect(button).toBeDisabled()
    fireEvent.click(button)
    expect(onContinue).not.toHaveBeenCalled()
  })

  it('mở "Tiếp tục thanh toán" khi da_nhap_thong_tin = true', () => {
    const onContinue = vi.fn()
    render(<BookingDetailsSummary booking={SAVED_BOOKING} onEdit={vi.fn()} onContinue={onContinue} />)

    fireEvent.click(screen.getByRole('button', { name: 'Tiếp tục thanh toán' }))

    expect(onContinue).toHaveBeenCalledOnce()
  })
})
