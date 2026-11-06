import { Link } from 'react-router-dom'

export default function NotFoundPage() {
  return (
    <section className="mx-auto max-w-sm rounded-2xl border border-slate-200/90 bg-white p-8 text-center shadow-xs space-y-3">
      <span className="inline-block text-4xl font-black text-brand-600">404</span>
      <h1 className="text-lg font-bold tracking-tight text-slate-900">404 – Không tìm thấy trang</h1>
      <p className="text-xs text-slate-500">Trang bạn tìm không tồn tại hoặc đã được di chuyển.</p>
      <div className="pt-2">
        <Link
          to="/"
          className="inline-flex items-center justify-center rounded-lg bg-brand-600 px-4 py-2 text-xs font-bold text-white shadow-2xs hover:bg-brand-700 transition-all"
        >
          Về trang chủ
        </Link>
      </div>
    </section>
  )
}
