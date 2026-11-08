import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'

import BrandLogo from '../components/BrandLogo'
import { PinIcon, SearchIcon, TicketIcon } from '../components/icons'
import { useAuth } from '../hooks/useAuth'
import { getHealth } from '../services/healthService'
import { APP_NAME, APP_TAGLINE, SERVICE_AREA } from '../utils/constants'

type BackendStatus =
  | { state: 'checking' }
  | { state: 'connected' }
  | { state: 'error'; message: string }

export default function HomePage() {
  const { user } = useAuth()
  const [backend, setBackend] = useState<BackendStatus>({ state: 'checking' })

  useEffect(() => {
    let cancelled = false
    getHealth()
      .then(() => {
        if (!cancelled) setBackend({ state: 'connected' })
      })
      .catch((error: unknown) => {
        if (!cancelled) {
          setBackend({ state: 'error', message: error instanceof Error ? error.message : String(error) })
        }
      })
    return () => {
      cancelled = true
    }
  }, [])

  return (
    <section className="space-y-6">
      {/* Hero Banner */}
      <div className="relative overflow-hidden rounded-3xl bg-gradient-to-br from-brand-700 via-brand-600 to-brand-800 p-6 sm:p-10 lg:p-12 text-white shadow-lg ring-1 ring-black/5">
        <div className="relative z-10 flex flex-col-reverse items-center justify-between gap-8 md:flex-row md:gap-12">
          <div className="flex-1 text-center md:text-left">
            <div className="inline-flex items-center gap-2 rounded-full bg-white/15 backdrop-blur-xs px-3.5 py-1 text-xs font-semibold text-brand-100 ring-1 ring-white/20 mb-4">
              <span className="h-1.5 w-1.5 rounded-full bg-amber-300" aria-hidden="true" />
              <span>{APP_TAGLINE}</span>
            </div>
            <h1 className="text-3xl font-extrabold tracking-tight sm:text-4xl lg:text-5xl leading-tight">
              {APP_NAME}
            </h1>
            <p className="mt-3 text-base text-brand-100 sm:text-lg max-w-xl leading-relaxed">
              Đặt vé xe {SERVICE_AREA} trực tuyến, trả tiền mặt khi lên xe.
            </p>
            <div className="mt-8 flex flex-wrap items-center justify-center gap-3 md:justify-start">
              <Link
                to="/tim-chuyen"
                className="inline-flex items-center gap-2.5 rounded-xl bg-amber-400 px-6 py-3.5 text-base font-bold text-slate-900 shadow-md transition-all hover:bg-amber-300 hover:shadow-lg active:scale-[0.98]"
              >
                <SearchIcon className="h-5 w-5" />
                Tìm chuyến ngay
              </Link>
              {user?.vai_tro === 'KHACH' ? (
                <Link
                  to="/ve-cua-toi"
                  className="inline-flex items-center gap-2 rounded-xl border border-white/30 bg-white/10 backdrop-blur-xs px-5 py-3.5 text-sm font-semibold text-white transition-colors hover:bg-white/20"
                >
                  <TicketIcon className="h-4 w-4" />
                  Vé của tôi
                </Link>
              ) : (
                <Link
                  to="/tra-cuu-ve"
                  className="inline-flex items-center gap-2 rounded-xl border border-white/30 bg-white/10 backdrop-blur-xs px-5 py-3.5 text-sm font-semibold text-white transition-colors hover:bg-white/20"
                >
                  <TicketIcon className="h-4 w-4" />
                  Tra cứu vé đã đặt
                </Link>
              )}
            </div>
          </div>

          <div className="flex shrink-0 items-center justify-center">
            <div className="flex h-36 w-36 sm:h-44 sm:w-44 items-center justify-center rounded-3xl bg-white p-4 shadow-2xl ring-4 ring-white/25">
              <BrandLogo className="h-full w-full object-contain" />
            </div>
          </div>
        </div>

        {/* Họa tiết nền trang trí */}
        <div
          aria-hidden="true"
          className="pointer-events-none absolute -right-16 -top-16 h-72 w-72 rounded-full bg-white/10 blur-2xl"
        />
        <div
          aria-hidden="true"
          className="pointer-events-none absolute -left-16 -bottom-16 h-72 w-72 rounded-full bg-brand-900/40 blur-2xl"
        />
      </div>

      {/* Thanh trạng thái hệ thống */}
      <div className="flex flex-col gap-2 rounded-2xl border border-slate-200/80 bg-white px-5 py-3 shadow-2xs sm:flex-row sm:items-center sm:justify-between text-xs sm:text-sm">
        <div className="flex items-center gap-2 text-slate-500 font-medium">
          <PinIcon className="h-4 w-4 text-brand-600 shrink-0" />
          <span>Tuyến kết nối: <strong className="text-slate-800 font-semibold">{SERVICE_AREA}</strong></span>
        </div>
        <p role="status" className="font-medium">
          {backend.state === 'checking' && (
            <span className="inline-flex items-center gap-2 text-slate-600">
              <span className="h-2 w-2 rounded-full bg-amber-400 animate-pulse" />
              Đang kiểm tra kết nối backend…
            </span>
          )}
          {backend.state === 'connected' && (
            <span className="inline-flex items-center gap-1.5 rounded-full bg-emerald-50 px-2.5 py-1 text-emerald-700 ring-1 ring-emerald-200/70">
              <span className="h-2 w-2 rounded-full bg-emerald-500" />
              Đã kết nối backend.
            </span>
          )}
          {backend.state === 'error' && (
            <span className="inline-flex items-center gap-1.5 rounded-full bg-rose-50 px-2.5 py-1 text-rose-700 ring-1 ring-rose-200/70">
              <span className="h-2 w-2 rounded-full bg-rose-500" />
              Không kết nối được backend: {backend.message}
            </span>
          )}
        </p>
      </div>
    </section>
  )
}
