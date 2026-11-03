import { Link, NavLink } from 'react-router-dom'

import { APP_NAME } from '../utils/constants'

const NAV_ITEMS = [
  { to: '/tim-chuyen', label: 'Tìm chuyến' },
  { to: '/tra-cuu-ve', label: 'Tra cứu vé' },
  { to: '/dang-nhap', label: 'Đăng nhập' },
]

export default function Header() {
  return (
    <header className="border-b border-slate-200 bg-white">
      <div className="mx-auto flex max-w-5xl flex-col gap-2 px-4 py-3 sm:flex-row sm:items-center sm:justify-between">
        <Link to="/" className="text-lg font-bold text-blue-700">
          {APP_NAME}
        </Link>
        <nav aria-label="Menu chính">
          <ul className="flex flex-wrap gap-x-4 gap-y-1 text-sm font-medium">
            {NAV_ITEMS.map((item) => (
              <li key={item.to}>
                <NavLink
                  to={item.to}
                  className={({ isActive }) =>
                    isActive ? 'text-blue-700 underline underline-offset-4' : 'text-slate-700 hover:text-blue-700'
                  }
                >
                  {item.label}
                </NavLink>
              </li>
            ))}
          </ul>
        </nav>
      </div>
    </header>
  )
}
