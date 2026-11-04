import { Link, NavLink } from 'react-router-dom'

import { useAuth } from '../hooks/useAuth'
import { APP_NAME } from '../utils/constants'

const NAV_ITEMS = [
  { to: '/tim-chuyen', label: 'Tìm chuyến' },
  { to: '/tra-cuu-ve', label: 'Tra cứu vé' },
]

function navClassName({ isActive }: { isActive: boolean }): string {
  return isActive ? 'text-blue-700 underline underline-offset-4' : 'text-slate-700 hover:text-blue-700'
}

export default function Header() {
  const { user, logout } = useAuth()

  return (
    <header className="border-b border-slate-200 bg-white">
      <div className="mx-auto flex max-w-5xl flex-col gap-2 px-4 py-3 sm:flex-row sm:items-center sm:justify-between">
        <Link to="/" className="text-lg font-bold text-blue-700">
          {APP_NAME}
        </Link>
        <nav aria-label="Menu chính">
          <ul className="flex flex-wrap items-center gap-x-4 gap-y-1 text-sm font-medium">
            {NAV_ITEMS.map((item) => (
              <li key={item.to}>
                <NavLink to={item.to} className={navClassName}>
                  {item.label}
                </NavLink>
              </li>
            ))}
            {user?.vai_tro === 'KHACH' && (
              <li>
                <NavLink to="/ve-cua-toi" className={navClassName}>
                  Vé của tôi
                </NavLink>
              </li>
            )}
            {user ? (
              <>
                <li className="text-slate-900">{user.ho_ten}</li>
                <li>
                  <button type="button" onClick={logout} className="text-slate-700 hover:text-blue-700">
                    Đăng xuất
                  </button>
                </li>
              </>
            ) : (
              <li>
                <NavLink to="/dang-nhap" className={navClassName}>
                  Đăng nhập
                </NavLink>
              </li>
            )}
          </ul>
        </nav>
      </div>
    </header>
  )
}
