import type { RouteObject } from 'react-router-dom'

import Layout from './components/Layout'
import RequireCustomer from './components/RequireCustomer'
import BookingPage from './pages/BookingPage'
import HomePage from './pages/HomePage'
import LoginPage from './pages/LoginPage'
import MyTicketsPage from './pages/MyTicketsPage'
import NotFoundPage from './pages/NotFoundPage'
import RegisterPage from './pages/RegisterPage'
import SeatSelectionPage from './pages/SeatSelectionPage'
import TraCuuVePage from './pages/TraCuuVePage'
import TripSearchPage from './pages/TripSearchPage'

export const routes: RouteObject[] = [
  {
    path: '/',
    element: <Layout />,
    children: [
      { index: true, element: <HomePage /> },
      { path: 'tim-chuyen', element: <TripSearchPage /> },
      { path: 'chuyen/:id', element: <SeatSelectionPage /> },
      { path: 'dat-ve/:maDon', element: <BookingPage /> },
      { path: 'tra-cuu-ve', element: <TraCuuVePage /> },
      // Đặt vé không cần đăng nhập (BR-BUS-01); chỉ "Vé của tôi" cần tài khoản khách (BR-BUS-36)
      {
        path: 've-cua-toi',
        element: (
          <RequireCustomer>
            <MyTicketsPage />
          </RequireCustomer>
        ),
      },
      { path: 'dang-nhap', element: <LoginPage /> },
      { path: 'dang-ky', element: <RegisterPage /> },
      { path: '*', element: <NotFoundPage /> },
    ],
  },
]
