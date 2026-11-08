import { createContext } from 'react'

import type { VaiTro } from '../services/authService'

/** Thông tin hiển thị của người đang đăng nhập; quyền thật do backend kiểm tra. */
export type AuthUser = {
  vai_tro: VaiTro
  ho_ten: string
}

export type AuthContextValue = {
  /** null là khách vãng lai. */
  user: AuthUser | null
  login: (ten_dang_nhap: string, mat_khau: string) => Promise<void>
  logout: () => void
}

export const AuthContext = createContext<AuthContextValue | null>(null)
