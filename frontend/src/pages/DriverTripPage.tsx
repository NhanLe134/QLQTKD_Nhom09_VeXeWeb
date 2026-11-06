import { useCallback, useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'

import InlineConfirm from '../components/InlineConfirm'
import {
  collectCash,
  completeTrip,
  getDriverTrip,
  submitCashDeposit,
  type DriverTripDetail,
  type Passenger,
} from '../services/driverService'
import {
  formatCurrency,
  formatDate,
  formatDateTime,
  formatDepositStatus,
  formatPaymentStatus,
  formatTime,
  formatTripStatus,
} from '../utils/format'

type State =
  | { state: 'loading' }
  | { state: 'loaded'; data: DriverTripDetail }
  | { state: 'error'; message: string }

type Pending = { kind: 'collect'; passenger: Passenger } | { kind: 'deposit' } | { kind: 'complete' } | null

const DEPOSIT_STYLES: Record<string, string> = {
  CHO_XAC_NHAN: 'bg-amber-50 text-amber-800 ring-amber-200',
  DA_XAC_NHAN: 'bg-emerald-50 text-emerald-800 ring-emerald-200',
  TU_CHOI: 'bg-rose-50 text-rose-800 ring-rose-200',
}

function errorText(error: unknown): string {
  return error instanceof Error ? error.message : String(error)
}

/**
 * Tài xế: khách của một chuyến → "Đã thu tiền mặt" từng vé → nộp tiền cho nhà xe.
 * Mọi số tiền do backend tính, trang chỉ hiển thị.
 */
export default function DriverTripPage() {
  const { id = '' } = useParams()
  const [result, setResult] = useState<State>({ state: 'loading' })
  const [pending, setPending] = useState<Pending>(null)
  const [message, setMessage] = useState('')
  const [done, setDone] = useState('')

  const load = useCallback(async () => {
    const data = await getDriverTrip(id)
    setResult({ state: 'loaded', data })
  }, [id])

  useEffect(() => {
    let cancelled = false
    getDriverTrip(id)
      .then((data) => {
        if (!cancelled) setResult({ state: 'loaded', data })
      })
      .catch((error: unknown) => {
        if (!cancelled) setResult({ state: 'error', message: errorText(error) })
      })
    return () => {
      cancelled = true
    }
  }, [id])

  async function run(action: () => Promise<string>) {
    setMessage('')
    setDone('')
    try {
      setDone(await action())
    } catch (error: unknown) {
      setMessage(errorText(error))
      // Dữ liệu có thể đã đổi (khách vừa hủy vé, đã có khoản chờ): tải lại để hiện đúng
      await load().catch(() => {})
    } finally {
      setPending(null)
    }
  }

  function collect(passenger: Passenger) {
    return run(async () => {
      setResult({ state: 'loaded', data: await collectCash(id, passenger.ve_id) })
      return `Đã ghi nhận thu tiền mặt ghế ${passenger.so_ghe}.`
    })
  }

  function deposit() {
    return run(async () => {
      const created = await submitCashDeposit(id)
      await load()
      return `Đã nộp ${formatCurrency(created.so_tien)}, chờ nhà xe xác nhận.`
    })
  }

  function complete() {
    return run(async () => {
      setResult({ state: 'loaded', data: await completeTrip(id) })
      return 'Đã kết thúc chuyến.'
    })
  }

  return (
    <section className="space-y-4">
      <Link to="/tai-xe" className="inline-block text-xs font-semibold text-brand-700 hover:underline">
        ← Chuyến của tôi
      </Link>

      {result.state === 'loading' && (
        <p role="status" className="text-xs text-slate-600">
          Đang tải chuyến…
        </p>
      )}

      {result.state === 'error' && (
        <p role="alert" className="rounded-xl bg-rose-50 p-3 text-xs font-semibold text-rose-700 ring-1 ring-rose-200/70">
          {result.message}
        </p>
      )}

      {result.state === 'loaded' && (
        <TripDetail
          data={result.data}
          pending={pending}
          message={message}
          done={done}
          onAsk={(next) => {
            setMessage('')
            setDone('')
            setPending(next)
          }}
          onCancel={() => setPending(null)}
          onCollect={collect}
          onDeposit={deposit}
          onComplete={complete}
        />
      )}
    </section>
  )
}

type DetailProps = {
  data: DriverTripDetail
  pending: Pending
  message: string
  done: string
  onAsk: (pending: Pending) => void
  onCancel: () => void
  onCollect: (passenger: Passenger) => Promise<void>
  onDeposit: () => Promise<void>
  onComplete: () => Promise<void>
}

function TripDetail({ data, pending, message, done, onAsk, onCancel, onCollect, onDeposit, onComplete }: DetailProps) {
  const { chuyen, tien_mat: cash } = data

  return (
    <>
      <div>
        <h1 className="text-xl sm:text-2xl font-bold tracking-tight text-slate-900">{chuyen.ten_tuyen}</h1>
        <p className="mt-0.5 text-xs text-slate-500">
          {formatTime(chuyen.gio_di)} ngày {formatDate(chuyen.ngay_khoi_hanh)} · {formatTripStatus(data.trang_thai)}
        </p>
      </div>

      {message && (
        <p role="alert" className="rounded-xl bg-rose-50 p-3 text-xs font-semibold text-rose-700 ring-1 ring-rose-200/70">
          {message}
        </p>
      )}
      {done && (
        <p role="status" className="rounded-xl bg-emerald-50 p-3 text-xs font-semibold text-emerald-800 ring-1 ring-emerald-200/70">
          {done}
        </p>
      )}

      <section aria-label="Tiền mặt" className="space-y-3 rounded-xl border border-slate-200/90 bg-white p-4 text-xs shadow-2xs">
        <h2 className="font-bold text-slate-900">Tiền mặt</h2>
        <dl className="grid grid-cols-2 gap-x-3 gap-y-1.5">
          <dt className="text-slate-500">Đã thu</dt>
          <dd className="text-right font-bold text-slate-900">{formatCurrency(cash.tong_da_thu)}</dd>
          <dt className="text-slate-500">Chưa thu</dt>
          <dd className="text-right font-semibold text-amber-700">{formatCurrency(cash.tong_chua_thu)}</dd>
          <dt className="text-slate-500">Đã nộp (đã xác nhận)</dt>
          <dd className="text-right text-slate-800">{formatCurrency(cash.da_nop)}</dd>
          <dt className="text-slate-500">Đang chờ xác nhận</dt>
          <dd className="text-right text-slate-800">{formatCurrency(cash.dang_cho)}</dd>
        </dl>

        {pending?.kind === 'deposit' ? (
          <InlineConfirm title="Nộp tiền cho nhà xe" confirmLabel="Nộp tiền" onConfirm={onDeposit} onCancel={onCancel}>
            Nộp <strong className="text-amber-700">{formatCurrency(cash.co_the_nop)}</strong> tiền mặt của chuyến cho nhà xe?
          </InlineConfirm>
        ) : (
          data.co_the_nop_tien && (
            <button
              type="button"
              onClick={() => onAsk({ kind: 'deposit' })}
              className="w-full rounded-lg bg-brand-600 px-4 py-2.5 text-sm font-bold text-white shadow-2xs hover:bg-brand-700"
            >
              Nộp tiền {formatCurrency(cash.co_the_nop)}
            </button>
          )
        )}

        {data.khoan_nop.length > 0 && (
          <ul aria-label="Khoản đã nộp" className="space-y-1.5 border-t border-slate-100 pt-2">
            {data.khoan_nop.map((item) => (
              <li key={item.nop_tien_id} className="flex flex-wrap items-center justify-between gap-1">
                <span className="text-slate-600">
                  {formatDateTime(item.ngay_nop)} · <strong className="text-slate-900">{formatCurrency(item.so_tien)}</strong>
                </span>
                <span className={`rounded-full px-2 py-0.5 font-semibold ring-1 ${DEPOSIT_STYLES[item.trang_thai] ?? ''}`}>
                  {formatDepositStatus(item.trang_thai)}
                </span>
              </li>
            ))}
          </ul>
        )}
      </section>

      <section aria-label="Danh sách khách" className="space-y-3">
        <h2 className="text-sm font-bold text-slate-900">Khách ({data.khach.length})</h2>
        {data.khach.length === 0 && (
          <p className="rounded-2xl border border-slate-200/90 bg-white p-5 text-center text-xs font-medium text-slate-600 shadow-2xs">
            Chuyến chưa có khách.
          </p>
        )}
        <ul className="space-y-3">
          {data.khach.map((passenger) => (
            <li
              key={passenger.ve_id}
              aria-label={`Ghế ${passenger.so_ghe}`}
              className="space-y-2 rounded-xl border border-slate-200/90 bg-white p-4 text-xs shadow-2xs"
            >
              <div className="flex items-center justify-between gap-2">
                <p className="font-bold text-slate-900">
                  Ghế {passenger.so_ghe} · {passenger.ho_ten ?? '—'}
                </p>
                {passenger.so_dien_thoai && (
                  <a href={`tel:${passenger.so_dien_thoai}`} className="font-semibold text-brand-700 hover:underline">
                    {passenger.so_dien_thoai}
                  </a>
                )}
              </div>
              <dl className="grid grid-cols-[auto_1fr] gap-x-3 gap-y-1">
                <dt className="text-slate-500">Đón</dt>
                <dd className="text-right text-slate-800 break-words">{passenger.diem_don ?? '—'}</dd>
                <dt className="text-slate-500">Trả</dt>
                <dd className="text-right text-slate-800 break-words">{passenger.diem_tra ?? '—'}</dd>
                <dt className="text-slate-500">Thanh toán</dt>
                <dd className="text-right font-semibold text-slate-800">{formatPaymentStatus(passenger.trang_thai_thanh_toan)}</dd>
                {passenger.so_tien_can_thu > 0 && (
                  <>
                    <dt className="font-bold text-slate-700">Cần thu</dt>
                    <dd className="text-right text-sm font-extrabold text-amber-600">
                      {formatCurrency(passenger.so_tien_can_thu)}
                    </dd>
                  </>
                )}
              </dl>
              {pending?.kind === 'collect' && pending.passenger.ve_id === passenger.ve_id ? (
                <InlineConfirm
                  title="Xác nhận đã thu tiền"
                  onConfirm={() => onCollect(passenger)}
                  onCancel={onCancel}
                >
                  Đã thu <strong className="text-amber-700">{formatCurrency(passenger.so_tien_can_thu)}</strong> của ghế{' '}
                  {passenger.so_ghe}?
                </InlineConfirm>
              ) : (
                passenger.co_the_thu_tien && (
                  <button
                    type="button"
                    onClick={() => onAsk({ kind: 'collect', passenger })}
                    className="w-full rounded-lg bg-brand-600 px-4 py-2 text-xs font-bold text-white shadow-2xs hover:bg-brand-700"
                  >
                    Đã thu tiền mặt
                  </button>
                )
              )}
            </li>
          ))}
        </ul>
      </section>

      {pending?.kind === 'complete' ? (
        <InlineConfirm title="Kết thúc chuyến" confirmLabel="Kết thúc" onConfirm={onComplete} onCancel={onCancel}>
          Xác nhận chuyến đã hoàn thành?
        </InlineConfirm>
      ) : (
        data.co_the_ket_thuc && (
          <button
            type="button"
            onClick={() => onAsk({ kind: 'complete' })}
            className="w-full rounded-lg border border-slate-300 bg-white px-4 py-2.5 text-sm font-semibold text-slate-700 hover:bg-slate-50"
          >
            Kết thúc chuyến
          </button>
        )
      )}
    </>
  )
}
