import { act, renderHook } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { useCountdown } from './useCountdown'

beforeEach(() => {
  vi.useFakeTimers()
  vi.setSystemTime(new Date('2026-12-01T03:15:00Z'))
})

afterEach(() => {
  vi.useRealTimers()
})

describe('useCountdown', () => {
  it('đếm ngược mỗi giây và dừng ở 0', () => {
    const { result } = renderHook(() => useCountdown('2026-12-01T03:20:00Z', 0))

    expect(result.current).toBe(300000)
    act(() => {
      vi.advanceTimersByTime(1000)
    })
    expect(result.current).toBe(299000)
    act(() => {
      vi.advanceTimersByTime(400000)
    })
    expect(result.current).toBe(0)
  })

  it('dùng độ lệch giờ server khi đồng hồ máy khách chạy nhanh', () => {
    // Máy khách nhanh hơn server 60 giây: offset = -60000
    vi.setSystemTime(new Date('2026-12-01T03:16:00Z'))

    const { result } = renderHook(() => useCountdown('2026-12-01T03:20:00Z', -60000))

    expect(result.current).toBe(300000)
  })

  it('không có hạn giữ thì trả null', () => {
    const { result } = renderHook(() => useCountdown(null, 0))

    expect(result.current).toBeNull()
  })
})
