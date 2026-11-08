import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import QrSePayPanel from './QrSePayPanel'
import type { QrSePay } from '../services/bookingService'

const QR: QrSePay = {
  ma_don: 'DH00100000',
  so_tien: 390000,
  noi_dung: 'THANH TOAN VE DH00100000',
  qr_url: 'https://img.vietqr.io/image/qr.png',
  thoi_gian_cho_giay: 300,
}

describe('QrSePayPanel', () => {
  it('hiện ảnh QR, số tiền và nội dung phải chuyển đúng', () => {
    render(<QrSePayPanel qr={QR} conLaiMs={4 * 60 * 1000 + 1000} />)

    expect(screen.getByTestId('qr-se-pay-hinh')).toHaveAttribute('src', QR.qr_url)
    expect(screen.getByTestId('qr-se-pay-so-tien')).toHaveTextContent('390.000 đ')
    expect(screen.getByTestId('qr-se-pay-noi-dung')).toHaveTextContent('THANH TOAN VE DH00100000')
    expect(screen.getByRole('timer', { name: 'Thời gian chuyển khoản còn lại' })).toHaveTextContent('04:01')
    expect(screen.queryByRole('alert')).not.toBeInTheDocument()
  })

  it('hết 5 phút: hiện cảnh báo, không còn đồng hồ', () => {
    render(<QrSePayPanel qr={QR} conLaiMs={0} />)

    const alert = screen.getByRole('alert')
    expect(alert).toHaveTextContent('Quá thời gian chuyển khoản')
    expect(screen.queryByRole('timer')).not.toBeInTheDocument()
  })
})
