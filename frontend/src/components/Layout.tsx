import { Outlet } from 'react-router-dom'

import { APP_TAGLINE, SERVICE_AREA } from '../utils/constants'
import Header from './Header'
import { PinIcon } from './icons'

// Điện thoại: thanh trên → menu ngang → nội dung → chân trang.
// Màn hình rộng (md): menu dọc bên trái, nội dung bên phải.
export default function Layout() {
  return (
    <div
      className="grid min-h-screen grid-cols-[minmax(0,1fr)] grid-rows-[auto_auto_1fr_auto] text-slate-900 [grid-template-areas:'header'_'nav'_'main'_'footer'] md:grid-cols-[220px_minmax(0,1fr)] md:grid-rows-[auto_1fr_auto] md:[grid-template-areas:'header_header'_'nav_main'_'nav_footer']"
    >
      <Header />
      <main className="min-w-0 px-4 py-6 [grid-area:main] md:px-8">
        <div className="mx-auto max-w-5xl">
          <Outlet />
        </div>
      </main>
      <footer className="bg-brand-600 px-4 py-3 text-sm text-white [grid-area:footer] md:px-8">
        <div className="mx-auto flex max-w-5xl flex-col items-center gap-1 sm:flex-row sm:justify-between">
          <span className="font-semibold">{APP_TAGLINE}</span>
          <span className="flex items-center gap-1">
            <PinIcon className="h-4 w-4" />
            {SERVICE_AREA}
          </span>
        </div>
      </footer>
    </div>
  )
}
