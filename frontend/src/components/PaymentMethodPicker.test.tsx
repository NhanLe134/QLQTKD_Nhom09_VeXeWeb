import { fireEvent, render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'

import PaymentMethodPicker from './PaymentMethodPicker'

describe('PaymentMethodPicker', () => {
  it('hiện tổng tiền backend trả, hai phương thức đều bấm được', () => {
    const onChooseCash = vi.fn()
    const onChooseTransfer = vi.fn()
    render(
      <PaymentMethodPicker
        tongTien={390000}
        onChooseCash={onChooseCash}
        onChooseTransfer={onChooseTransfer}
        transferActive={false}
        onBack={vi.fn()}
      />,
    )

    expect(screen.getByTestId('tong-tien-thanh-toan')).toHaveTextContent('390.000 đ')
    fireEvent.click(screen.getByRole('button', { name: /Tiền mặt khi lên xe/ }))
    expect(onChooseCash).toHaveBeenCalledOnce()
    fireEvent.click(screen.getByRole('button', { name: /Chuyển khoản SePay/ }))
    expect(onChooseTransfer).toHaveBeenCalledOnce()
  })

  it('đang chọn chuyển khoản: nút được tô, chờ QR thì vô hiệu', () => {
    render(
      <PaymentMethodPicker
        tongTien={1}
        onChooseCash={vi.fn()}
        onChooseTransfer={vi.fn()}
        transferActive={true}
        transferLoading={true}
        onBack={vi.fn()}
      />,
    )

    expect(screen.getByRole('button', { name: /Chuyển khoản SePay/ })).toBeDisabled()
    expect(screen.getByRole('button', { name: /Chuyển khoản SePay/ })).toHaveAttribute('aria-pressed', 'true')
    expect(screen.getByText('Đang tạo mã QR…')).toBeInTheDocument()
  })

  it('panel QR render phía dưới hai ô phương thức', () => {
    render(
      <PaymentMethodPicker
        tongTien={1}
        onChooseCash={vi.fn()}
        onChooseTransfer={vi.fn()}
        transferActive={true}
        onBack={vi.fn()}
      >
        <div data-testid="qr-slot">QR ở đây</div>
      </PaymentMethodPicker>,
    )

    expect(screen.getByTestId('qr-slot')).toBeInTheDocument()
    expect(screen.getByText('QR ở đây')).toBeInTheDocument()
  })

  it('bấm quay lại gọi onBack', () => {
    const onBack = vi.fn()
    render(
      <PaymentMethodPicker
        tongTien={1}
        onChooseCash={vi.fn()}
        onChooseTransfer={vi.fn()}
        transferActive={false}
        onBack={onBack}
      />,
    )

    fireEvent.click(screen.getByRole('button', { name: 'Quay lại thông tin hành khách' }))

    expect(onBack).toHaveBeenCalledOnce()
  })
})
