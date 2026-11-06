import type { ReactNode } from 'react'
import { Navigate, useLocation } from 'react-router-dom'

import { useAuth } from '../hooks/useAuth'

/**
 * Trang chỉ dành cho khách đã đăng nhập (vai trò KHACH). Chưa đăng nhập thì chuyển tới
 * trang đăng nhập, đăng nhập xong quay lại. Quyền thật do backend kiểm tra (401/403).
 */
export default function RequireCustomer({ children }: { children: ReactNode }) {
  const { user } = useAuth()
  const location = useLocation()

  if (!user) {
    return <Navigate to="/dang-nhap" replace state={{ from: location.pathname }} />
  }
  if (user.vai_tro !== 'KHACH') {
    return (
      <p role="alert" className="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700">
        Trang này chỉ dành cho tài khoản khách hàng.
      </p>
    )
  }
  return <>{children}</>
}
