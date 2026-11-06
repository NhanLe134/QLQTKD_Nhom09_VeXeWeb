import { Link, NavLink } from 'react-router-dom'

import { useAuth } from '../hooks/useAuth'
import { APP_NAME } from '../utils/constants'
import BrandLogo from './BrandLogo'
import { HomeIcon, LookupIcon, SearchIcon, SwapIcon, TicketIcon, UserIcon } from './icons'

type NavItem = { to: string; label: string; icon: (props: { className?: string }) => React.ReactNode; end?: boolean }

const NAV_ITEMS: NavItem[] = [
  { to: '/', label: 'Trang chủ', icon: HomeIcon, end: true },
  { to: '/tim-chuyen', label: 'Tìm chuyến', icon: SearchIcon },
  { to: '/tra-cuu-ve', label: 'Tra cứu vé', icon: LookupIcon },
]

// "Vé của tôi" chỉ dành cho tài khoản khách (BR-BUS-36)
const CUSTOMER_ITEM: NavItem = { to: '/ve-cua-toi', label: 'Vé của tôi', icon: TicketIcon }

// Hoàn tiền thủ công cho vé đã hủy: chỉ tài khoản nhà xe
const OPERATOR_ITEM: NavItem = { to: '/nha-xe/hoan-tien', label: 'Hoàn tiền', icon: SwapIcon }

function navItemsFor(vaiTro: string | undefined): NavItem[] {
  if (vaiTro === 'KHACH') return [NAV_ITEMS[0], NAV_ITEMS[1], CUSTOMER_ITEM]
  if (vaiTro === 'NHA_XE') return [...NAV_ITEMS, OPERATOR_ITEM]
  return NAV_ITEMS
}

function navClassName({ isActive }: { isActive: boolean }): string {
  const base =
    'flex items-center gap-1.5 rounded-xl px-3 py-1.5 text-xs font-semibold transition-all duration-150 sm:text-sm sm:px-3.5 sm:py-2'
  return isActive
    ? `${base} bg-brand-50 text-brand-700 shadow-2xs ring-1 ring-brand-200/80`
    : `${base} text-slate-600 hover:bg-slate-100 hover:text-slate-900`
}

/**
 * Thanh điều hướng chính (Header):
 * Hiển thị logo, menu điều hướng và trạng thái tài khoản.
 */
export default function Header() {
  const { user, logout } = useAuth()
  // Đã đăng nhập tài khoản khách: hiển thị "Vé của tôi", ẩn "Tra cứu vé". Chưa đăng nhập: hiển thị "Tra cứu vé".
  // Nhà xe: thêm "Hoàn tiền"
  const items = navItemsFor(user?.vai_tro)

  return (
    <header className="sticky top-0 z-40 border-b border-slate-200/80 bg-white/95 backdrop-blur-md shadow-2xs">
      <div className="mx-auto max-w-6xl px-4 sm:px-6 lg:px-8">
        <div className="flex flex-col gap-2 py-2.5 md:h-16 md:flex-row md:items-center md:justify-between md:gap-4 md:py-0">
          <div className="flex items-center justify-between">
            <Link to="/" className="flex items-center gap-2.5">
              <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-brand-50 p-1 ring-1 ring-brand-100 shadow-2xs">
                <BrandLogo className="h-full w-full object-contain" />
              </span>
              <span className="text-base font-bold tracking-tight text-slate-900 sm:text-lg">
                {APP_NAME}
              </span>
            </Link>

            {/* Tài khoản trên mobile */}
            <div className="flex items-center gap-2 md:hidden">
              {user ? (
                <div className="flex items-center gap-2 text-xs">
                  <span className="flex max-w-[100px] items-center gap-1 truncate rounded-full bg-slate-100 px-2 py-1 font-medium text-slate-700">
                    <UserIcon className="h-3.5 w-3.5 shrink-0 text-brand-600" />
                    <span className="truncate">{user.ho_ten}</span>
                  </span>
                  <button
                    type="button"
                    onClick={logout}
                    className="rounded-lg border border-slate-200 px-2 py-1 text-xs font-semibold text-slate-600 hover:bg-red-50 hover:text-red-600"
                  >
                    Đăng xuất
                  </button>
                </div>
              ) : (
                <NavLink
                  to="/dang-nhap"
                  className="flex items-center gap-1.5 rounded-lg bg-brand-600 px-3 py-1.5 text-xs font-semibold text-white shadow-2xs hover:bg-brand-700"
                >
                  <UserIcon className="h-3.5 w-3.5" />
                  Đăng nhập
                </NavLink>
              )}
            </div>
          </div>

          {/* Menu chính */}
          <nav aria-label="Menu chính" className="min-w-0">
            <ul className="flex items-center justify-start gap-1 overflow-x-auto py-0.5 md:justify-center">
              {items.map((item) => (
                <li key={item.to} className="shrink-0">
                  <NavLink to={item.to} end={item.end} className={navClassName}>
                    <item.icon className="h-4 w-4 shrink-0" />
                    <span>{item.label}</span>
                  </NavLink>
                </li>
              ))}
            </ul>
          </nav>

          {/* Tài khoản trên desktop */}
          <div className="hidden items-center gap-3 md:flex">
            {user ? (
              <>
                <span className="flex items-center gap-2 rounded-full bg-slate-100 px-3 py-1.5 text-sm font-medium text-slate-800">
                  <UserIcon className="h-4 w-4 shrink-0 text-brand-600" />
                  <span className="max-w-[140px] truncate">{user.ho_ten}</span>
                </span>
                <button
                  type="button"
                  onClick={logout}
                  className="rounded-xl border border-slate-200 px-3 py-1.5 text-xs font-semibold text-slate-600 transition-colors hover:border-red-200 hover:bg-red-50 hover:text-red-600"
                >
                  Đăng xuất
                </button>
              </>
            ) : (
              <NavLink
                to="/dang-nhap"
                className="flex items-center gap-2 rounded-xl bg-brand-600 px-4 py-2 text-sm font-semibold text-white shadow-xs transition-all hover:bg-brand-700 active:scale-[0.98]"
              >
                <UserIcon className="h-4 w-4" />
                Đăng nhập
              </NavLink>
            )}
          </div>
        </div>
      </div>
    </header>
  )
}
