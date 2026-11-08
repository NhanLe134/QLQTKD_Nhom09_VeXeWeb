import { Outlet } from 'react-router-dom'

import { APP_TAGLINE, SERVICE_AREA } from '../utils/constants'
import Header from './Header'
import { PinIcon } from './icons'

export default function Layout() {
  return (
    <div className="flex min-h-screen flex-col bg-slate-50 text-slate-800 antialiased">
      <Header />
      <main className="flex-1 w-full px-4 py-6 sm:px-6 md:py-8 lg:px-8">
        <div className="mx-auto max-w-5xl">
          <Outlet />
        </div>
      </main>
      <footer className="mt-auto border-t border-slate-200 bg-white py-5 px-4 text-sm text-slate-600 sm:px-6 lg:px-8">
        <div className="mx-auto flex max-w-5xl flex-col items-center justify-between gap-3 text-center sm:flex-row sm:text-left">
          <div className="flex items-center gap-2 font-medium text-slate-700">
            <span className="h-2 w-2 rounded-full bg-brand-600" aria-hidden="true" />
            <span>{APP_TAGLINE}</span>
          </div>
          <div className="flex items-center gap-1.5 text-slate-500">
            <PinIcon className="h-4 w-4 text-brand-600" />
            <span>
              Khu vực phục vụ: <strong className="font-semibold text-slate-700">{SERVICE_AREA}</strong>
            </span>
          </div>
        </div>
      </footer>
    </div>
  )
}
