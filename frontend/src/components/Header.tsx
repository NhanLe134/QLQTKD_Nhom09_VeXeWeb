import { Link, NavLink } from 'react-router-dom'

import { useAuth } from '../hooks/useAuth'
import { APP_NAME } from '../utils/constants'
import { BusLogo, HomeIcon, LookupIcon, SearchIcon, TicketIcon, UserIcon } from './icons'

type NavItem = { to: string; label: string; icon: (props: { className?: string }) => React.ReactNode; end?: boolean }

const NAV_ITEMS: NavItem[] = [
  { to: '/', label: 'Trang chủ', icon: HomeIcon, end: true },
  { to: '/tim-chuyen', label: 'Tìm chuyến', icon: SearchIcon },
  { to: '/tra-cuu-ve', label: 'Tra cứu vé', icon: LookupIcon },
]

// "Vé của tôi" chỉ dành cho tài khoản khách (BR-BUS-36)
const CUSTOMER_ITEM: NavItem = { to: '/ve-cua-toi', label: 'Vé của tôi', icon: TicketIcon }

function navClassName({ isActive }: { isActive: boolean }): string {
  // Điện thoại: icon trên, chữ dưới, các ô chia đều; màn hình rộng: icon bên trái chữ
  const base =
    'flex flex-col items-center gap-1 rounded-lg px-1 py-1.5 text-center text-xs font-medium transition-colors md:flex-row md:gap-3 md:px-3 md:py-2.5 md:text-left md:text-sm'
  return isActive
    ? `${base} bg-brand-100 text-brand-800 shadow-sm`
    : `${base} text-slate-700 hover:bg-brand-50 hover:text-brand-700`
}

/**
 * Thanh trên (logo, tài khoản) và menu chính. Trả về hai khối để Layout xếp:
 * điện thoại menu nằm ngang dưới thanh trên, màn hình rộng menu nằm dọc bên trái.
 */
export default function Header() {
  const { user, logout } = useAuth()
  const items = user?.vai_tro === 'KHACH' ? [NAV_ITEMS[0], NAV_ITEMS[1], CUSTOMER_ITEM, NAV_ITEMS[2]] : NAV_ITEMS

  return (
    <>
      <header className="bg-brand-600 text-white shadow-md [grid-area:header]">
        <div className="flex items-center justify-between gap-3 px-4 py-3 md:px-6">
          <Link to="/" className="flex min-w-0 items-center gap-3">
            <BusLogo className="h-10 w-10 shrink-0 text-brand-600" />
            <span className="truncate text-lg font-bold tracking-wide uppercase md:text-xl">{APP_NAME}</span>
          </Link>
          <div className="flex min-w-0 items-center gap-3 text-sm font-medium">
            {user ? (
              <>
                <span className="flex min-w-0 items-center gap-2">
                  <UserIcon className="h-7 w-7 shrink-0 rounded-full bg-white p-1 text-brand-600" />
                  <span className="max-w-[7rem] truncate sm:max-w-none">{user.ho_ten}</span>
                </span>
                <button
                  type="button"
                  onClick={logout}
                  className="rounded-lg border border-white/60 px-3 py-1.5 hover:bg-white/15"
                >
                  Đăng xuất
                </button>
              </>
            ) : (
              <NavLink
                to="/dang-nhap"
                className="flex items-center gap-2 rounded-lg bg-white px-3 py-1.5 text-brand-700 hover:bg-brand-50"
              >
                <UserIcon className="h-4 w-4" />
                Đăng nhập
              </NavLink>
            )}
          </div>
        </div>
      </header>
      <nav
        aria-label="Menu chính"
        className="min-w-0 border-b border-brand-100 bg-white [grid-area:nav] md:border-r md:border-b-0"
      >
        <ul className="grid auto-cols-fr grid-flow-col gap-1 px-2 py-2 md:flex md:flex-col md:gap-2 md:px-3 md:py-5">
          {items.map((item) => (
            <li key={item.to}>
              <NavLink to={item.to} end={item.end} className={navClassName}>
                <item.icon className="h-5 w-5 md:h-6 md:w-6" />
                {item.label}
              </NavLink>
            </li>
          ))}
        </ul>
      </nav>
    </>
  )
}
