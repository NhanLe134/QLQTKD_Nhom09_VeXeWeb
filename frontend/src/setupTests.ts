import '@testing-library/jest-dom/vitest'
import { cleanup } from '@testing-library/react'
import { afterEach } from 'vitest'

import { setAuthToken, setUnauthorizedHandler } from './services/apiClient'

afterEach(() => {
  cleanup()
  // Phiên đăng nhập là trạng thái dùng chung giữa các test: xóa sau mỗi test
  sessionStorage.clear()
  setAuthToken(null)
  setUnauthorizedHandler(null)
})
