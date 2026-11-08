import { useCallback, useEffect, useId, useRef, useState } from 'react'

import { ApiError } from '../services/apiClient'
import {
  type CancelQuoteTicket,
  type CancelReceipt,
  cancelTickets,
  getCancelQuote,
  type Ticket,
} from '../services/bookingService'
import { formatCurrency } from '../utils/format'

type Props = {
  maDon: string
  ticket: Ticket
  onCancelled: (receipt: CancelReceipt) => void
  onClose: () => void
}

type QuoteState =
  | { state: 'loading' }
  | { state: 'loaded'; quote: CancelQuoteTicket }
  | { state: 'error'; message: string }

type FieldName = 'ngan_hang_nhan' | 'so_tai_khoan_nhan'

const inputClass =
  'w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 outline-none focus:border-brand-500 focus:ring-2 focus:ring-brand-100'

/**
 * Hủy một vé đã xác nhận: mức hoàn và quyền hủy do backend tính (cổng "Được phép hủy?"),
 * frontend chỉ hiển thị. Xác nhận bằng hộp ngay trong trang, không dùng window.confirm.
 */
export default function CancelTicketPanel({ maDon, ticket, onCancelled, onClose }: Props) {
  const [quote, setQuote] = useState<QuoteState>({ state: 'loading' })
  const [bank, setBank] = useState('')
  const [account, setAccount] = useState('')
  const [fieldErrors, setFieldErrors] = useState<Partial<Record<FieldName, string>>>({})
  const [confirming, setConfirming] = useState(false)
  const [submitting, setSubmitting] = useState(false)
  const [message, setMessage] = useState('')
  // Chặn bấm liên tiếp trước khi kịp render lại nút vô hiệu
  const inFlight = useRef(false)
  const titleId = useId()
  const confirmTitleId = useId()
  const bankId = useId()
  const accountId = useId()

  const fetchQuote = useCallback(
    (isCurrent: () => boolean = () => true) => {
      getCancelQuote(maDon)
        .then((data) => {
          if (!isCurrent()) return
          const found = data.ve.find((ve) => ve.ve_id === ticket.ve_id)
          setQuote(found ? { state: 'loaded', quote: found } : { state: 'error', message: 'Không tìm thấy vé' })
        })
        .catch((error: unknown) => {
          if (isCurrent()) setQuote({ state: 'error', message: error instanceof Error ? error.message : String(error) })
        })
    },
    [maDon, ticket.ve_id],
  )

  useEffect(() => {
    let current = true
    fetchQuote(() => current)
    return () => {
      current = false
    }
  }, [fetchQuote])

  function reloadQuote() {
    setQuote({ state: 'loading' })
    fetchQuote()
  }

  function next(needsAccount: boolean) {
    // Chỉ báo sớm ô trống; định dạng do backend kiểm tra và trả lỗi đúng ô
    if (needsAccount) {
      const errors: Partial<Record<FieldName, string>> = {}
      if (!bank.trim()) errors.ngan_hang_nhan = 'Vui lòng nhập ngân hàng nhận tiền hoàn'
      if (!account.trim()) errors.so_tai_khoan_nhan = 'Vui lòng nhập số tài khoản nhận tiền hoàn'
      setFieldErrors(errors)
      if (Object.keys(errors).length > 0) return
    }
    setMessage('')
    setConfirming(true)
  }

  async function confirm(quoted: CancelQuoteTicket) {
    if (inFlight.current) return
    inFlight.current = true
    setSubmitting(true)
    setMessage('')
    try {
      const receipt = await cancelTickets(maDon, {
        ve_ids: [quoted.ve_id],
        muc_hoan_xac_nhan: quoted.muc_hoan,
        ...(quoted.can_tai_khoan_nhan ? { ngan_hang_nhan: bank, so_tai_khoan_nhan: account } : {}),
      })
      onCancelled(receipt)
    } catch (error: unknown) {
      inFlight.current = false
      setSubmitting(false)
      setConfirming(false)
      const detail = error instanceof Error ? error.message : String(error)
      if (error instanceof ApiError && (error.field === 'ngan_hang_nhan' || error.field === 'so_tai_khoan_nhan')) {
        setFieldErrors({ [error.field]: detail })
        return
      }
      setMessage(detail)
      // Mức hoàn đổi hoặc vé vừa thay đổi: tải lại số liệu mới từ backend
      if (error instanceof ApiError && error.status === 409) reloadQuote()
    }
  }

  return (
    <section
      aria-labelledby={titleId}
      className="space-y-3 rounded-2xl border border-rose-200 bg-rose-50/60 p-4 shadow-2xs"
    >
      <div className="flex items-start justify-between gap-2">
        <h2 id={titleId} className="text-sm font-bold text-slate-900">
          Hủy vé {ticket.ve_id} – Ghế {ticket.so_ghe}
        </h2>
        <button
          type="button"
          onClick={onClose}
          disabled={submitting}
          className="shrink-0 rounded-lg px-2 py-1 text-xs font-semibold text-slate-600 hover:bg-white disabled:opacity-50"
        >
          Đóng
        </button>
      </div>

      {quote.state === 'loading' && (
        <p role="status" className="text-xs text-slate-600">
          Đang kiểm tra điều kiện hủy…
        </p>
      )}

      {quote.state === 'error' && (
        <p role="alert" className="text-xs font-semibold text-rose-700">
          {quote.message}
        </p>
      )}

      {message && (
        <p role="alert" className="rounded-lg bg-white p-2.5 text-xs font-semibold text-rose-700 ring-1 ring-rose-200">
          {message}
        </p>
      )}

      {quote.state === 'loaded' && !quote.quote.duoc_huy && (
        <p role="alert" className="rounded-lg bg-white p-2.5 text-xs font-semibold text-rose-700 ring-1 ring-rose-200">
          {quote.quote.ly_do}
        </p>
      )}

      {quote.state === 'loaded' && quote.quote.duoc_huy && (
        <>
          <dl className="grid grid-cols-2 gap-x-3 gap-y-1.5 rounded-xl bg-white p-3 text-xs ring-1 ring-slate-200/80">
            <dt className="text-slate-500">Giá vé</dt>
            <dd className="text-right font-semibold text-slate-800">{formatCurrency(quote.quote.gia_ve)}</dd>
            <dt className="text-slate-500">Mức hoàn theo thời điểm hủy</dt>
            <dd className="text-right font-semibold text-slate-800">{quote.quote.ti_le_hoan}%</dd>
            <dt className="font-bold text-slate-700">Số tiền hoàn</dt>
            <dd data-testid="muc-hoan" className="text-right text-sm font-extrabold text-amber-600">
              {formatCurrency(quote.quote.muc_hoan)}
            </dd>
          </dl>
          {quote.quote.ghi_chu && <p className="text-xs text-slate-600">{quote.quote.ghi_chu}</p>}

          {quote.quote.can_tai_khoan_nhan && !confirming && (
            <div className="space-y-2.5">
              <p className="text-xs text-slate-600">Nhập tài khoản để nhà xe chuyển tiền hoàn cho bạn.</p>
              <div className="space-y-1">
                <label htmlFor={bankId} className="text-xs font-semibold text-slate-700">
                  Ngân hàng nhận tiền
                </label>
                <input
                  id={bankId}
                  value={bank}
                  onChange={(e) => setBank(e.target.value)}
                  maxLength={100}
                  aria-invalid={fieldErrors.ngan_hang_nhan ? true : undefined}
                  className={inputClass}
                />
                {fieldErrors.ngan_hang_nhan && (
                  <p className="text-xs font-semibold text-rose-700">{fieldErrors.ngan_hang_nhan}</p>
                )}
              </div>
              <div className="space-y-1">
                <label htmlFor={accountId} className="text-xs font-semibold text-slate-700">
                  Số tài khoản
                </label>
                <input
                  id={accountId}
                  value={account}
                  onChange={(e) => setAccount(e.target.value)}
                  inputMode="numeric"
                  maxLength={20}
                  aria-invalid={fieldErrors.so_tai_khoan_nhan ? true : undefined}
                  className={inputClass}
                />
                {fieldErrors.so_tai_khoan_nhan && (
                  <p className="text-xs font-semibold text-rose-700">{fieldErrors.so_tai_khoan_nhan}</p>
                )}
              </div>
            </div>
          )}

          {!confirming && (
            <button
              type="button"
              onClick={() => next(quote.quote.can_tai_khoan_nhan)}
              className="w-full rounded-lg bg-rose-600 px-4 py-2 text-xs font-bold text-white shadow-2xs hover:bg-rose-700 sm:w-auto"
            >
              Tiếp tục hủy vé
            </button>
          )}

          {confirming && (
            <div
              role="alertdialog"
              aria-labelledby={confirmTitleId}
              className="space-y-3 rounded-xl border border-rose-300 bg-white p-3.5"
            >
              <p id={confirmTitleId} className="text-xs font-bold uppercase tracking-wider text-rose-800">
                Xác nhận hủy vé
              </p>
              <p className="text-xs text-slate-700">
                Vé {quote.quote.ve_id} (ghế {quote.quote.so_ghe}) sẽ bị hủy và không thể khôi phục. Số tiền hoàn:{' '}
                <strong className="font-bold text-amber-700">{formatCurrency(quote.quote.muc_hoan)}</strong>.
              </p>
              <div className="flex flex-wrap gap-2">
                <button
                  type="button"
                  onClick={() => confirm(quote.quote)}
                  disabled={submitting}
                  className="rounded-lg bg-rose-600 px-4 py-1.5 text-xs font-bold text-white shadow-2xs hover:bg-rose-700 disabled:opacity-50"
                >
                  {submitting ? 'Đang hủy…' : 'Đồng ý hủy vé'}
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
        </>
      )}
    </section>
  )
}
