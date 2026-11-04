import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'

import { BusLogo, SearchIcon } from '../components/icons'

import { getHealth } from '../services/healthService'
import { APP_NAME, SERVICE_AREA } from '../utils/constants'

type BackendStatus =
  | { state: 'checking' }
  | { state: 'connected' }
  | { state: 'error'; message: string }

export default function HomePage() {
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
      <div className="flex flex-col items-center gap-4 rounded-2xl bg-white p-6 text-center shadow-md ring-1 ring-brand-100 sm:flex-row sm:text-left">
        <BusLogo className="h-24 w-24 shrink-0 text-brand-600" />
        <div className="space-y-2">
          <h1 className="text-2xl font-bold text-brand-800">{APP_NAME}</h1>
          <p className="text-slate-600">Đặt vé xe {SERVICE_AREA} trực tuyến, trả tiền mặt khi lên xe.</p>
          <Link
            to="/tim-chuyen"
            className="inline-flex items-center gap-2 rounded-lg bg-brand-700 px-5 py-2.5 font-semibold text-white shadow-sm hover:bg-brand-800"
          >
            <SearchIcon className="h-4 w-4" />
            Tìm chuyến ngay
          </Link>
        </div>
      </div>
      <p role="status" className="rounded-lg bg-white px-3 py-2 text-sm shadow-sm ring-1 ring-brand-100">
        {backend.state === 'checking' && 'Đang kiểm tra kết nối backend…'}
        {backend.state === 'connected' && <span className="text-green-700">Đã kết nối backend.</span>}
        {backend.state === 'error' && (
          <span className="text-red-700">Không kết nối được backend: {backend.message}</span>
        )}
      </p>
    </section>
  )
}
