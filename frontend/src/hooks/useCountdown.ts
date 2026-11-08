import { useEffect, useState } from 'react'

const TICK_MS = 1000

/**
 * Số ms còn lại tới `deadline` (ISO, giờ server).
 * `clockOffsetMs` = giờ server − giờ máy khách lúc nhận dữ liệu, để đồng hồ máy khách lệch vẫn đếm đúng.
 * Mỗi nhịp tính lại từ Date.now() nên tab bị tạm dừng cũng không lệch dồn.
 */
export function useCountdown(deadline: string | null, clockOffsetMs: number): number | null {
  const [now, setNow] = useState(() => Date.now())
  const deadlineMs = deadline ? Date.parse(deadline) : null

  useEffect(() => {
    if (deadlineMs === null) return
    const timer = setInterval(() => {
      const current = Date.now()
      setNow(current)
      if (current + clockOffsetMs >= deadlineMs) {
        clearInterval(timer)
      }
    }, TICK_MS)
    return () => clearInterval(timer)
  }, [deadlineMs, clockOffsetMs])

  if (deadlineMs === null) {
    return null
  }
  return Math.max(0, deadlineMs - (now + clockOffsetMs))
}
