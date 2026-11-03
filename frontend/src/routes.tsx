import type { RouteObject } from 'react-router-dom'

import Layout from './components/Layout'
import HomePage from './pages/HomePage'
import NotFoundPage from './pages/NotFoundPage'
import UnderConstructionPage from './pages/UnderConstructionPage'

export const routes: RouteObject[] = [
  {
    path: '/',
    element: <Layout />,
    children: [
      { index: true, element: <HomePage /> },
      { path: 'tim-chuyen', element: <UnderConstructionPage title="Tìm chuyến" /> },
      { path: 'tra-cuu-ve', element: <UnderConstructionPage title="Tra cứu vé" /> },
      { path: 'dang-nhap', element: <UnderConstructionPage title="Đăng nhập" /> },
      { path: '*', element: <NotFoundPage /> },
    ],
  },
]
