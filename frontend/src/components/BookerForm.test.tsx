import { fireEvent, render, screen } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import AuthProvider, { AUTH_STORAGE_KEY } from '../context/AuthProvider'
import BookerForm from './BookerForm'

const fetchMock = vi.fn<typeof fetch>()

const ME = {
  user_id: 'TK00000001',
  ten_dang_nhap: 'khach_mau',
  vai_tro: 'KHACH',
  so_dien_thoai: '0900000001',
  khach_hang: {
    khach_hang_id: 'KH00000001',
    ho_ten: 'Khách Mẫu',
    email: 'khach@vexe.example',
    so_dien_thoai: '0900000001',
    ngay_dang_ky: '2026-11-01T00:00:00Z',
  },
}

function renderForm() {
  const onSubmit = vi.fn()
  const onCancel = vi.fn()
  render(
    <AuthProvider>
      <BookerForm onSubmit={onSubmit} onCancel={onCancel} submitting={false} />
    </AuthProvider>,
  )
  return { onSubmit, onCancel }
}

function fill(label: string, value: string) {
  fireEvent.change(screen.getByLabelText(label), { target: { value } })
}

beforeEach(() => {
  vi.stubEnv('VITE_API_URL', 'http://api.test')
  vi.stubGlobal('fetch', fetchMock)
})

afterEach(() => {
  fetchMock.mockReset()
  vi.unstubAllEnvs()
  vi.unstubAllGlobals()
})

describe('BookerForm — khách vãng lai', () => {
  it('báo lỗi tại từng ô khi thiếu họ tên, SĐT sai, email sai', () => {
    const { onSubmit } = renderForm()

    fill('Số điện thoại', '12345')
    fill('Email', 'khong-phai-email')
    fireEvent.click(screen.getByRole('button', { name: 'Xác nhận giữ ghế' }))

    expect(screen.getByText('Vui lòng nhập họ tên')).toBeInTheDocument()
    expect(screen.getByText('Số điện thoại gồm 10 chữ số, bắt đầu bằng 0')).toBeInTheDocument()
    expect(screen.getByText('Email không hợp lệ')).toBeInTheDocument()
    expect(screen.getByLabelText('Số điện thoại')).toHaveAttribute('aria-invalid', 'true')
    expect(onSubmit).not.toHaveBeenCalled()
  })

  it.each(['', '   '])('email bắt buộc: để trống %j thì báo lỗi, không gửi', (value) => {
    const { onSubmit } = renderForm()

    fill('Họ tên', 'Trần Thị Bình')
    fill('Số điện thoại', '0905111222')
    fill('Email', value)
    fireEvent.click(screen.getByRole('button', { name: 'Xác nhận giữ ghế' }))

    expect(screen.getByText('Vui lòng nhập email')).toBeInTheDocument()
    expect(screen.getByLabelText('Email')).toHaveAttribute('aria-invalid', 'true')
    expect(onSubmit).not.toHaveBeenCalled()
  })

  it('gửi thông tin đã bỏ khoảng trắng, kèm email', () => {
    const { onSubmit } = renderForm()

    fill('Họ tên', '  Trần Thị Bình ')
    fill('Số điện thoại', '0905111222')
    fill('Email', ' binh@example.com ')
    fireEvent.click(screen.getByRole('button', { name: 'Xác nhận giữ ghế' }))

    expect(onSubmit).toHaveBeenCalledWith({
      ho_ten: 'Trần Thị Bình',
      so_dien_thoai: '0905111222',
      email: 'binh@example.com',
    })
  })

  it('nút Hủy gọi onCancel', () => {
    const { onCancel } = renderForm()

    fireEvent.click(screen.getByRole('button', { name: 'Hủy' }))

    expect(onCancel).toHaveBeenCalled()
  })
})

describe('BookerForm — đã đăng nhập', () => {
  beforeEach(() => {
    sessionStorage.setItem(
      AUTH_STORAGE_KEY,
      JSON.stringify({ token: 'tok', ho_ten: 'Khách Mẫu', vai_tro: 'KHACH' }),
    )
    fetchMock.mockImplementation(async () => new Response(JSON.stringify(ME), { status: 200 }))
  })

  it('tự điền thông tin tài khoản, không có ô nhập, xác nhận gửi null', async () => {
    const { onSubmit } = renderForm()

    expect(await screen.findByText('Khách Mẫu')).toBeInTheDocument()
    expect(screen.getByText('0900000001')).toBeInTheDocument()
    expect(screen.getByText('khach@vexe.example')).toBeInTheDocument()
    expect(screen.queryByLabelText('Số điện thoại')).not.toBeInTheDocument()

    fireEvent.click(screen.getByRole('button', { name: 'Xác nhận giữ ghế' }))

    expect(onSubmit).toHaveBeenCalledWith(null)
    expect(screen.queryByRole('note')).not.toBeInTheDocument()
  })

  it('tài khoản cũ chưa có email: báo không gửi được vé qua email, vẫn giữ ghế được', async () => {
    const noEmail = { ...ME, khach_hang: { ...ME.khach_hang, email: null } }
    fetchMock.mockImplementation(async () => new Response(JSON.stringify(noEmail), { status: 200 }))
    const { onSubmit } = renderForm()

    expect(await screen.findByRole('note')).toHaveTextContent('Tài khoản chưa có email nên vé sẽ không được gửi qua email.')
    fireEvent.click(screen.getByRole('button', { name: 'Xác nhận giữ ghế' }))

    expect(onSubmit).toHaveBeenCalledWith(null)
  })
})
