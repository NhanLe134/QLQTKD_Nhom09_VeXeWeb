import { useEffect, useState } from 'react'

import { getHealth } from '../services/healthService'
import { APP_NAME } from '../utils/constants'

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
    <section className="space-y-4">
      <h1 className="text-2xl font-bold">{APP_NAME}</h1>
      <p className="text-slate-600">Đặt vé xe Đà Nẵng – Hội An – Huế trực tuyến.</p>
      <p role="status" className="rounded-md border border-slate-200 bg-white px-3 py-2 text-sm">
        {backend.state === 'checking' && 'Đang kiểm tra kết nối backend…'}
        {backend.state === 'connected' && <span className="text-green-700">Đã kết nối backend.</span>}
        {backend.state === 'error' && (
          <span className="text-red-700">Không kết nối được backend: {backend.message}</span>
        )}
      </p>
    </section>
  )
}
