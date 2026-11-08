import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import HoldCountdown from './HoldCountdown'

// Đếm ngược theo thời gian thật nằm ở useCountdown.test.ts và BookingPage.test.tsx
describe('HoldCountdown', () => {
  it('hiện thời gian còn lại, chưa cảnh báo khi còn hơn 2 phút', () => {
    render(<HoldCountdown remainingMs={121000} />)

    expect(screen.getByRole('timer')).toHaveTextContent('02:01')
    expect(screen.queryByRole('alert')).not.toBeInTheDocument()
  })

  it('còn 2:00 thì hiện cảnh báo (BR-BUS-17)', () => {
    render(<HoldCountdown remainingMs={120000} />)

    expect(screen.getByRole('timer')).toHaveTextContent('02:00')
    expect(screen.getByRole('alert')).toHaveTextContent('Sắp hết thời gian giữ chỗ')
  })

  it.each([0, null])('còn %s thì hiện "Hết thời gian giữ chỗ"', (remainingMs) => {
    render(<HoldCountdown remainingMs={remainingMs} />)

    expect(screen.queryByRole('timer')).not.toBeInTheDocument()
    expect(screen.getByRole('alert')).toHaveTextContent('Hết thời gian giữ chỗ')
  })
})
