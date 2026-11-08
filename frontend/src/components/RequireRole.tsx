import type { ReactNode } from 'react'
import { Navigate, useLocation } from 'react-router-dom'

import { useAuth } from '../hooks/useAuth'
import type { VaiTro } from '../services/authService'

type Props = {
  role: VaiTro
  /** Thông báo khi đăng nhập sai vai trò */
  deniedMessage: string
  children: ReactNode
}

/**
 * Trang chỉ dành cho một vai trò. Chưa đăng nhập thì chuyển tới trang đăng nhập, đăng nhập
 * xong quay lại. Quyền thật do backend kiểm tra (401/403).
 */
export default function RequireRole({ role, deniedMessage, children }: Props) {
  const { user } = useAuth()
  const location = useLocation()

  if (!user) {
    return <Navigate to="/dang-nhap" replace state={{ from: location.pathname }} />
  }
  if (user.vai_tro !== role) {
    return (
      <p role="alert" className="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700">
        {deniedMessage}
      </p>
    )
  }
  return <>{children}</>
}
