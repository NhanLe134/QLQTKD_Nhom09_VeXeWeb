import type { RouteObject } from 'react-router-dom'

import Layout from './components/Layout'
import RequireCustomer from './components/RequireCustomer'
import RequireRole from './components/RequireRole'
import BookingPage from './pages/BookingPage'
import CashDepositsPage from './pages/CashDepositsPage'
import DriverTripPage from './pages/DriverTripPage'
import DriverTripsPage from './pages/DriverTripsPage'
import HomePage from './pages/HomePage'
import LoginPage from './pages/LoginPage'
import MyTicketsPage from './pages/MyTicketsPage'
import NotFoundPage from './pages/NotFoundPage'
import RefundsPage from './pages/RefundsPage'
import RegisterPage from './pages/RegisterPage'
import SeatSelectionPage from './pages/SeatSelectionPage'
import TraCuuVePage from './pages/TraCuuVePage'
import TripAssignmentPage from './pages/TripAssignmentPage'
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
      // Hoàn tiền thủ công cho vé đã hủy: chỉ tài khoản nhà xe
      {
        path: 'nha-xe/hoan-tien',
        element: (
          <RequireRole role="NHA_XE" deniedMessage="Trang này chỉ dành cho tài khoản nhà xe.">
            <RefundsPage />
          </RequireRole>
        ),
      },
      // Phân công tài xế và đối soát tiền mặt: chỉ tài khoản nhà xe
      {
        path: 'nha-xe/phan-cong',
        element: (
          <RequireRole role="NHA_XE" deniedMessage="Trang này chỉ dành cho tài khoản nhà xe.">
            <TripAssignmentPage />
          </RequireRole>
        ),
      },
      {
        path: 'nha-xe/doi-soat-tien-mat',
        element: (
          <RequireRole role="NHA_XE" deniedMessage="Trang này chỉ dành cho tài khoản nhà xe.">
            <CashDepositsPage />
          </RequireRole>
        ),
      },
      // Chuyến được phân công, thu và nộp tiền mặt: chỉ tài khoản tài xế
      {
        path: 'tai-xe',
        element: (
          <RequireRole role="TAI_XE" deniedMessage="Trang này chỉ dành cho tài khoản tài xế.">
            <DriverTripsPage />
          </RequireRole>
        ),
      },
      {
        path: 'tai-xe/chuyen/:id',
        element: (
          <RequireRole role="TAI_XE" deniedMessage="Trang này chỉ dành cho tài khoản tài xế.">
            <DriverTripPage />
          </RequireRole>
        ),
      },
      { path: 'dang-nhap', element: <LoginPage /> },
      { path: 'dang-ky', element: <RegisterPage /> },
      { path: '*', element: <NotFoundPage /> },
    ],
  },
]
