import { fireEvent, render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { describe, expect, it, vi } from 'vitest'

import type { CancelReceipt as Receipt } from '../services/bookingService'
import { CANCEL_RECEIPT } from '../utils/testBookings'
import CancelReceipt from './CancelReceipt'

function renderReceipt(receipt: Receipt, onDone?: () => void) {
  render(
    <MemoryRouter>
      <CancelReceipt receipt={receipt} onDone={onDone} />
    </MemoryRouter>,
  )
}

describe('CancelReceipt', () => {
  it('chờ hoàn tiền: số tiền, trạng thái, tài khoản đã che từ backend', () => {
    const onDone = vi.fn()
    renderReceipt(CANCEL_RECEIPT, onDone)

    expect(screen.getByRole('heading', { name: 'Hủy vé thành công' })).toBeInTheDocument()
    const item = screen.getByRole('listitem', { name: 'Vé đã hủy VE00100001' })
    expect(item).toHaveTextContent('Chờ hoàn tiền')
    expect(item).toHaveTextContent('99.000 đ')
    expect(screen.getByTestId('tong-hoan')).toHaveTextContent('99.000 đ')
    expect(screen.getByText(/Vietcombank \*\*\*\*6789/)).toBeInTheDocument()
    expect(screen.getByRole('status')).toHaveTextContent('Nhà xe sẽ chuyển khoản')

    fireEvent.click(screen.getByRole('button', { name: 'Xem vé còn lại' }))
    expect(onDone).toHaveBeenCalled()
  })

  it('không hoàn tiền: hiện "Không hoàn tiền", không có tài khoản, không có nút quay lại', () => {
    renderReceipt({
      ...CANCEL_RECEIPT,
      ve: [{ ...CANCEL_RECEIPT.ve[0], muc_hoan: 0, trang_thai_hoan: 'KHONG_HOAN_TIEN' }],
      tong_hoan: 0,
      ngan_hang_nhan: null,
      so_tai_khoan_nhan: null,
    })

    expect(screen.getByRole('listitem', { name: 'Vé đã hủy VE00100001' })).toHaveTextContent('Không hoàn tiền')
    expect(screen.getByTestId('tong-hoan')).toHaveTextContent('0 đ')
    expect(screen.queryByText(/Tài khoản nhận/)).not.toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Xem vé còn lại' })).not.toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'Về trang chủ' })).toHaveAttribute('href', '/')
  })
})
