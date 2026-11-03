import { type ReactNode, useCallback, useEffect, useMemo, useState } from 'react'

import { setAuthToken, setUnauthorizedHandler } from '../services/apiClient'
import * as authService from '../services/authService'
import { AuthContext, type AuthUser } from './AuthContext'

// sessionStorage: còn sau khi tải lại trang, tự xóa khi đóng tab (quyết định Task #5).
// Chỉ lưu token và thông tin hiển thị, không lưu mật khẩu.
export const AUTH_STORAGE_KEY = 'vexe.auth'

type StoredSession = AuthUser & { token: string }

function readStoredSession(): StoredSession | null {
  try {
    const raw = sessionStorage.getItem(AUTH_STORAGE_KEY)
    if (!raw) {
      return null
    }
    const parsed = JSON.parse(raw) as Partial<StoredSession>
    if (typeof parsed.token !== 'string' || typeof parsed.ho_ten !== 'string' || !parsed.vai_tro) {
      return null
    }
    return { token: parsed.token, ho_ten: parsed.ho_ten, vai_tro: parsed.vai_tro }
  } catch {
    return null
  }
}

function writeStoredSession(session: StoredSession | null): void {
  try {
    if (session) {
      sessionStorage.setItem(AUTH_STORAGE_KEY, JSON.stringify(session))
    } else {
      sessionStorage.removeItem(AUTH_STORAGE_KEY)
    }
  } catch {
    // Trình duyệt chặn storage: phiên chỉ còn trong bộ nhớ
  }
}

export default function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(() => {
    const stored = readStoredSession()
    // Gắn token ngay khi khởi tạo: effect của trang con chạy trước effect của Provider
    setAuthToken(stored?.token ?? null)
    return stored ? { ho_ten: stored.ho_ten, vai_tro: stored.vai_tro } : null
  })

  const logout = useCallback(() => {
    setAuthToken(null)
    writeStoredSession(null)
    setUser(null)
  }, [])

  const login = useCallback(async (ten_dang_nhap: string, mat_khau: string) => {
    const result = await authService.login({ ten_dang_nhap, mat_khau })
    const session: StoredSession = {
      token: result.access_token,
      ho_ten: result.ho_ten,
      vai_tro: result.vai_tro,
    }
    setAuthToken(session.token)
    writeStoredSession(session)
    setUser({ ho_ten: session.ho_ten, vai_tro: session.vai_tro })
  }, [])

  useEffect(() => {
    setUnauthorizedHandler(logout)
    return () => setUnauthorizedHandler(null)
  }, [logout])

  // Phiên lấy lại từ sessionStorage có thể đã hết hạn: hỏi backend, 401 thì handler tự đăng xuất.
  // Giá trị cố định từ lúc khởi tạo nên chỉ kiểm tra một lần.
  const [restoredOnMount] = useState(() => user !== null)
  useEffect(() => {
    if (restoredOnMount) {
      authService.getMe().catch(() => {})
    }
  }, [restoredOnMount])

  const value = useMemo(() => ({ user, login, logout }), [user, login, logout])

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}
