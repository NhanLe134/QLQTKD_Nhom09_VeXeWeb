import { useEffect, useId, useRef, useState } from 'react'

import { ApiError } from '../services/apiClient'
import { getPendingRefunds, markRefunded, type Refund } from '../services/refundService'
import { formatCurrency, formatDate, formatDateTime, formatTime } from '../utils/format'

type State =
  | { state: 'loading' }
  | { state: 'loaded'; data: Refund[] }
  | { state: 'error'; message: string }

/** Nhà xe: khoản hoàn tiền chờ chuyển khoản thủ công, đánh dấu "Đã hoàn" bằng mã giao dịch. */
export default function RefundsPage() {
  const [result, setResult] = useState<State>({ state: 'loading' })
  const [activeId, setActiveId] = useState<string | null>(null)
  const [done, setDone] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false
    getPendingRefunds()
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

  function handleRefunded(refund: Refund) {
    setActiveId(null)
    setDone(`Đã đánh dấu hoàn ${formatCurrency(refund.so_tien)} cho vé ${refund.ve_id}.`)
    setResult((current) =>
      current.state === 'loaded'
        ? { state: 'loaded', data: current.data.filter((item) => item.thanh_toan_id !== refund.thanh_toan_id) }
        : current,
    )
  }

  return (
    <section className="space-y-4">
      <div>
        <h1 className="text-xl sm:text-2xl font-bold tracking-tight text-slate-900">Hoàn tiền</h1>
        <p className="mt-0.5 text-xs text-slate-500">
          Khoản hoàn cho vé khách đã hủy. Chuyển khoản cho khách rồi nhập mã giao dịch ngân hàng.
        </p>
      </div>

      {done && (
        <p role="status" className="rounded-xl bg-emerald-50 p-3 text-xs font-semibold text-emerald-800 ring-1 ring-emerald-200/70">
          {done}
        </p>
      )}

      {result.state === 'loading' && (
        <p role="status" className="text-xs text-slate-600">
          Đang tải khoản hoàn…
        </p>
      )}

      {result.state === 'error' && (
        <p role="alert" className="rounded-xl bg-rose-50 p-3 text-xs font-semibold text-rose-700 ring-1 ring-rose-200/70">
          {result.message}
        </p>
      )}

      {result.state === 'loaded' && result.data.length === 0 && (
        <p className="rounded-2xl border border-slate-200/90 bg-white p-5 text-center text-xs font-medium text-slate-600 shadow-2xs">
          Không có khoản hoàn nào đang chờ.
        </p>
      )}

      {result.state === 'loaded' && result.data.length > 0 && (
        <ul aria-label="Khoản chờ hoàn" className="space-y-3">
          {result.data.map((refund) => (
            <li
              key={refund.thanh_toan_id}
              aria-label={`Khoản hoàn ${refund.thanh_toan_id}`}
              className="space-y-2.5 rounded-xl border border-slate-200/90 bg-white p-4 text-xs shadow-2xs"
            >
              <div className="flex flex-wrap items-center justify-between gap-1 border-b border-slate-100 pb-2">
                <p className="font-bold text-slate-900">{refund.chuyen.ten_tuyen}</p>
                <p className="text-slate-500">
                  {formatTime(refund.chuyen.gio_di)} ngày {formatDate(refund.chuyen.ngay_khoi_hanh)}
                </p>
              </div>
              <dl className="grid grid-cols-2 gap-x-3 gap-y-1.5">
                <dt className="text-slate-500">Mã đơn / vé</dt>
                <dd className="text-right font-mono font-semibold text-slate-800 break-all">
                  {refund.ma_don} / {refund.ve_id}
                </dd>
                <dt className="text-slate-500">Ghế</dt>
                <dd className="text-right font-semibold text-slate-800">{refund.so_ghe}</dd>
                <dt className="text-slate-500">Hủy lúc</dt>
                <dd className="text-right text-slate-700">{formatDateTime(refund.ngay_huy)}</dd>
                <dt className="text-slate-500">Ngân hàng</dt>
                <dd className="text-right font-semibold text-slate-800 break-words">{refund.ngan_hang_nhan ?? '—'}</dd>
                <dt className="text-slate-500">Số tài khoản</dt>
                <dd className="text-right font-mono font-semibold text-slate-800 break-all">
                  {refund.so_tai_khoan_nhan ?? '—'}
                </dd>
                <dt className="font-bold text-slate-700">Số tiền hoàn</dt>
                <dd className="text-right text-sm font-extrabold text-amber-600">{formatCurrency(refund.so_tien)}</dd>
              </dl>

              {activeId === refund.thanh_toan_id ? (
                <MarkRefundedForm
                  refund={refund}
                  onCancel={() => setActiveId(null)}
                  onDone={handleRefunded}
                />
              ) : (
                <div className="flex justify-end">
                  <button
                    type="button"
                    onClick={() => {
                      setDone(null)
                      setActiveId(refund.thanh_toan_id)
                    }}
                    className="rounded-lg bg-brand-600 px-4 py-1.5 text-xs font-bold text-white shadow-2xs hover:bg-brand-700"
                  >
                    Đã hoàn
                  </button>
                </div>
              )}
            </li>
          ))}
        </ul>
      )}
    </section>
  )
}

type FormProps = {
  refund: Refund
  onCancel: () => void
  onDone: (refund: Refund) => void
}

function MarkRefundedForm({ refund, onCancel, onDone }: FormProps) {
  const [code, setCode] = useState('')
  const [fieldError, setFieldError] = useState('')
  const [message, setMessage] = useState('')
  const [confirming, setConfirming] = useState(false)
  const [submitting, setSubmitting] = useState(false)
  const inFlight = useRef(false)
  const inputId = useId()
  const titleId = useId()

  function next() {
    if (!code.trim()) {
      setFieldError('Vui lòng nhập mã giao dịch ngân hàng')
      return
    }
    setFieldError('')
    setConfirming(true)
  }

  async function confirm() {
    if (inFlight.current) return
    inFlight.current = true
    setSubmitting(true)
    setMessage('')
    try {
      onDone(await markRefunded(refund.thanh_toan_id, code.trim()))
    } catch (error: unknown) {
      inFlight.current = false
      setSubmitting(false)
      setConfirming(false)
      const detail = error instanceof Error ? error.message : String(error)
      if (error instanceof ApiError && error.field === 'ma_giao_dich') {
        setFieldError(detail)
        return
      }
      setMessage(detail)
    }
  }

  return (
    <div className="space-y-2.5 border-t border-slate-100 pt-2.5">
      {message && (
        <p role="alert" className="font-semibold text-rose-700">
          {message}
        </p>
      )}
      {!confirming ? (
        <>
          <div className="space-y-1">
            <label htmlFor={inputId} className="font-semibold text-slate-700">
              Mã giao dịch ngân hàng
            </label>
            <input
              id={inputId}
              value={code}
              onChange={(e) => setCode(e.target.value)}
              maxLength={50}
              aria-invalid={fieldError ? true : undefined}
              className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 outline-none focus:border-brand-500 focus:ring-2 focus:ring-brand-100"
            />
            {fieldError && <p className="font-semibold text-rose-700">{fieldError}</p>}
          </div>
          <div className="flex flex-wrap gap-2">
            <button
              type="button"
              onClick={next}
              className="rounded-lg bg-brand-600 px-4 py-1.5 text-xs font-bold text-white shadow-2xs hover:bg-brand-700"
            >
              Tiếp tục
            </button>
            <button
              type="button"
              onClick={onCancel}
              className="rounded-lg border border-slate-300 bg-white px-3.5 py-1.5 text-xs font-semibold text-slate-700 hover:bg-slate-50"
            >
              Bỏ qua
            </button>
          </div>
        </>
      ) : (
        <div role="alertdialog" aria-labelledby={titleId} className="space-y-2.5 rounded-xl border border-brand-200 bg-brand-50/70 p-3">
          <p id={titleId} className="font-bold uppercase tracking-wider text-brand-900">
            Xác nhận đã hoàn tiền
          </p>
          <p className="text-slate-700">
            Đã chuyển <strong className="text-amber-700">{formatCurrency(refund.so_tien)}</strong> cho vé {refund.ve_id}, mã
            giao dịch <strong className="font-mono">{code.trim()}</strong>?
          </p>
          <div className="flex flex-wrap gap-2">
            <button
              type="button"
              onClick={confirm}
              disabled={submitting}
              className="rounded-lg bg-brand-600 px-4 py-1.5 text-xs font-bold text-white shadow-2xs hover:bg-brand-700 disabled:opacity-50"
            >
              {submitting ? 'Đang lưu…' : 'Đồng ý'}
            </button>
            <button
              type="button"
              onClick={() => setConfirming(false)}
              disabled={submitting}
              className="rounded-lg border border-slate-300 bg-white px-3.5 py-1.5 text-xs font-semibold text-slate-700 hover:bg-slate-50 disabled:opacity-50"
            >
              Quay lại
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
