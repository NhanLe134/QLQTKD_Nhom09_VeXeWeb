import { fireEvent, render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'

import PaymentMethodPicker from './PaymentMethodPicker'

describe('PaymentMethodPicker', () => {
  it('hiện tổng tiền backend trả, tiền mặt bấm được, chuyển khoản vô hiệu "Sắp có"', () => {
    const onChooseCash = vi.fn()
    render(<PaymentMethodPicker tongTien={390000} onChooseCash={onChooseCash} onBack={vi.fn()} />)

    expect(screen.getByTestId('tong-tien-thanh-toan')).toHaveTextContent('390.000 đ')
    const transfer = screen.getByRole('button', { name: /Chuyển khoản SePay/ })
    expect(transfer).toBeDisabled()
    expect(transfer).toHaveTextContent('Sắp có')

    fireEvent.click(screen.getByRole('button', { name: /Tiền mặt khi lên xe/ }))
    expect(onChooseCash).toHaveBeenCalledOnce()
  })

  it('bấm quay lại gọi onBack', () => {
    const onBack = vi.fn()
    render(<PaymentMethodPicker tongTien={1} onChooseCash={vi.fn()} onBack={onBack} />)

    fireEvent.click(screen.getByRole('button', { name: 'Quay lại thông tin hành khách' }))

    expect(onBack).toHaveBeenCalledOnce()
  })
})
