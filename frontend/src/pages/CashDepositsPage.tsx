import { useEffect, useState } from 'react'

import InlineConfirm from '../components/InlineConfirm'
import {
  confirmCashDeposit,
  getCashDeposits,
  rejectCashDeposit,
  type CashDeposit,
} from '../services/operatorService'
import { formatCurrency, formatDate, formatDateTime, formatTime } from '../utils/format'

type State =
  | { state: 'loading' }
  | { state: 'loaded'; data: CashDeposit[] }
  | { state: 'error'; message: string }

type Decision = 'confirm' | 'reject'

/** Nhà xe: khoản tiền mặt tài xế nộp đang chờ; Xác nhận (đã nhận tiền) hoặc Từ chối. */
export default function CashDepositsPage() {
  const [result, setResult] = useState<State>({ state: 'loading' })
  const [done, setDone] = useState('')

  useEffect(() => {
    let cancelled = false
    getCashDeposits('CHO_XAC_NHAN')
      .then((data) => {
        if (!cancelled) setResult({ state: 'loaded', data })
      })
      .catch((error: unknown) => {
        if (!cancelled) setResult({ state: 'error', message: error instanceof Error ? error.message : String(error) })
      })
    return () => {
      cancelled = true
    }
  }, [])

  function handleDecided(deposit: CashDeposit) {
    const verb = deposit.trang_thai === 'DA_XAC_NHAN' ? 'Đã xác nhận' : 'Đã từ chối'
    setDone(`${verb} khoản nộp ${formatCurrency(deposit.so_tien)} của ${deposit.ten_tai_xe ?? deposit.tai_xe_id}.`)
    setResult((current) =>
      current.state === 'loaded'
        ? { state: 'loaded', data: current.data.filter((item) => item.nop_tien_id !== deposit.nop_tien_id) }
        : current,
    )
  }

  return (
    <section className="space-y-4">
      <div>
        <h1 className="text-xl sm:text-2xl font-bold tracking-tight text-slate-900">Đối soát tiền mặt</h1>
        <p className="mt-0.5 text-xs text-slate-500">
          Khoản tiền mặt tài xế đã nộp. Kiểm tra tiền nhận được rồi Xác nhận, hoặc Từ chối để tài xế nộp lại.
        </p>
      </div>

      {done && (
        <p role="status" className="rounded-xl bg-emerald-50 p-3 text-xs font-semibold text-emerald-800 ring-1 ring-emerald-200/70">
          {done}
        </p>
      )}

      {result.state === 'loading' && (
        <p role="status" className="text-xs text-slate-600">
          Đang tải khoản nộp…
        </p>
      )}

      {result.state === 'error' && (
        <p role="alert" className="rounded-xl bg-rose-50 p-3 text-xs font-semibold text-rose-700 ring-1 ring-rose-200/70">
          {result.message}
        </p>
      )}

      {result.state === 'loaded' && result.data.length === 0 && (
        <p className="rounded-2xl border border-slate-200/90 bg-white p-5 text-center text-xs font-medium text-slate-600 shadow-2xs">
          Không có khoản nộp nào đang chờ xác nhận.
        </p>
      )}

      {result.state === 'loaded' && result.data.length > 0 && (
        <ul aria-label="Khoản nộp chờ xác nhận" className="space-y-3">
          {result.data.map((deposit) => (
            <DepositCard
              key={deposit.nop_tien_id}
              deposit={deposit}
              onDecided={handleDecided}
              onAsk={() => setDone('')}
            />
          ))}
        </ul>
      )}
    </section>
  )
}

type CardProps = {
  deposit: CashDeposit
  onDecided: (deposit: CashDeposit) => void
  onAsk: () => void
}

function DepositCard({ deposit, onDecided, onAsk }: CardProps) {
  const [decision, setDecision] = useState<Decision | null>(null)
  const [message, setMessage] = useState('')
  const { chuyen } = deposit
  const driverName = deposit.ten_tai_xe ?? deposit.tai_xe_id

  async function decide(kind: Decision) {
    setMessage('')
    try {
      const saved = kind === 'confirm' ? await confirmCashDeposit(deposit.nop_tien_id) : await rejectCashDeposit(deposit.nop_tien_id)
      onDecided(saved)
    } catch (error: unknown) {
      setDecision(null)
      setMessage(error instanceof Error ? error.message : String(error))
    }
  }

  return (
    <li
      aria-label={`Khoản nộp ${deposit.nop_tien_id}`}
      className="space-y-2.5 rounded-xl border border-slate-200/90 bg-white p-4 text-xs shadow-2xs"
    >
      <div className="flex flex-wrap items-center justify-between gap-1 border-b border-slate-100 pb-2">
        <p className="font-bold text-slate-900">{chuyen.ten_tuyen}</p>
        <p className="text-slate-500">
          {formatTime(chuyen.gio_di)} ngày {formatDate(chuyen.ngay_khoi_hanh)}
        </p>
      </div>
      <dl className="grid grid-cols-2 gap-x-3 gap-y-1.5">
        <dt className="text-slate-500">Tài xế</dt>
        <dd className="text-right font-semibold text-slate-800">{driverName}</dd>
        <dt className="text-slate-500">Mã chuyến</dt>
        <dd className="text-right font-mono text-slate-800">{chuyen.chuyen_xe_id}</dd>
        <dt className="text-slate-500">Ngày nộp</dt>
        <dd className="text-right text-slate-700">{formatDateTime(deposit.ngay_nop)}</dd>
        <dt className="font-bold text-slate-700">Số tiền</dt>
        <dd className="text-right text-sm font-extrabold text-amber-600">{formatCurrency(deposit.so_tien)}</dd>
      </dl>

      {message && (
        <p role="alert" className="font-semibold text-rose-700">
          {message}
        </p>
      )}

      {decision === 'confirm' && (
        <InlineConfirm title="Xác nhận đã nhận tiền" confirmLabel="Xác nhận" onConfirm={() => decide('confirm')} onCancel={() => setDecision(null)}>
          Đã nhận đủ <strong className="text-amber-700">{formatCurrency(deposit.so_tien)}</strong> từ {driverName}?
        </InlineConfirm>
      )}
      {decision === 'reject' && (
        <InlineConfirm
          title="Từ chối khoản nộp"
          confirmLabel="Từ chối"
          tone="danger"
          onConfirm={() => decide('reject')}
          onCancel={() => setDecision(null)}
        >
          Từ chối khoản {formatCurrency(deposit.so_tien)} của {driverName}? Tài xế sẽ phải nộp lại.
        </InlineConfirm>
      )}
      {decision === null && (
        <div className="flex gap-2">
          <button
            type="button"
            onClick={() => {
              onAsk()
              setDecision('confirm')
            }}
            className="flex-1 rounded-lg bg-brand-600 px-4 py-2 text-xs font-bold text-white shadow-2xs hover:bg-brand-700 sm:flex-none"
          >
            Xác nhận
          </button>
          <button
            type="button"
            onClick={() => {
              onAsk()
              setDecision('reject')
            }}
            className="flex-1 rounded-lg border border-rose-300 bg-white px-4 py-2 text-xs font-bold text-rose-700 hover:bg-rose-50 sm:flex-none"
          >
            Từ chối
          </button>
        </div>
      )}
    </li>
  )
}
