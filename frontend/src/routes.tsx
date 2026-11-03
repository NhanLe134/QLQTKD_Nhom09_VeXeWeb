import type { RouteObject } from 'react-router-dom'

import Layout from './components/Layout'
import HomePage from './pages/HomePage'
import LoginPage from './pages/LoginPage'
import NotFoundPage from './pages/NotFoundPage'
import RegisterPage from './pages/RegisterPage'
import UnderConstructionPage from './pages/UnderConstructionPage'

export const routes: RouteObject[] = [
  {
    path: '/',
    element: <Layout />,
    children: [
      { index: true, element: <HomePage /> },
      { path: 'tim-chuyen', element: <UnderConstructionPage title="Tìm chuyến" /> },
      { path: 'tra-cuu-ve', element: <UnderConstructionPage title="Tra cứu vé" /> },
      // Không trang nào yêu cầu đăng nhập (BR-BUS-01)
      { path: 'dang-nhap', element: <LoginPage /> },
      { path: 'dang-ky', element: <RegisterPage /> },
      { path: '*', element: <NotFoundPage /> },
    ],
  },
]
