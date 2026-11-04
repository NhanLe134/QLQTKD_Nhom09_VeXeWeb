import { fireEvent, render, screen, within } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import type { Booking, BookingDetailsRequest } from '../services/bookingService'
import { saveStoredBooking } from '../utils/bookingStorage'
import { HELD_BOOKING, jsonResponse, SAVED_BOOKING, ticket } from '../utils/testBookings'
import BookingDetailsForm from './BookingDetailsForm'

const fetchMock = vi.fn<typeof fetch>()
const onSaved = vi.fn()
const onGone = vi.fn()

function renderForm(booking: Booking = HELD_BOOKING) {
  render(<BookingDetailsForm booking={booking} onSaved={onSaved} onGone={onGone} />)
}

function seat(code: string) {
  return screen.getByRole('group', { name: `Ghế ${code}` })
}

function sentBody(): BookingDetailsRequest {
  const [, init] = fetchMock.mock.calls[0]
  return JSON.parse(String(init?.body)) as BookingDetailsRequest
}

function options(label: string): string[] {
  const select = screen.getByLabelText(label)
  return within(select)
    .getAllByRole('option')
    .map((option) => option.textContent ?? '')
}

function submit() {
  fireEvent.click(screen.getByRole('button', { name: 'Lưu thông tin' }))
}

beforeEach(() => {
  vi.stubEnv('VITE_API_URL', 'http://api.test')
  vi.stubGlobal('fetch', fetchMock)
  saveStoredBooking({ ma_don: 'DH00100000', ma_truy_cap: 'ma-bi-mat' })
})

afterEach(() => {
  fetchMock.mockReset()
  onSaved.mockReset()
  onGone.mockReset()
  vi.unstubAllEnvs()
  vi.unstubAllGlobals()
  sessionStorage.clear()
})

describe('BookingDetailsForm', () => {
  it('điền sẵn hành khách từ vé và điểm đón/trả theo điểm đi, điểm đến', () => {
    renderForm()

    for (const code of ['A01', 'A02']) {
      const group = seat(code)
      expect(within(group).getByRole('checkbox', { name: 'Giống người đặt' })).toBeChecked()
      expect(within(group).getByLabelText('Họ tên')).toHaveValue('Trần Thị Bình')
      expect(within(group).getByLabelText('Họ tên')).toBeDisabled()
      expect(within(group).getByLabelText('Số điện thoại')).toHaveValue('0905111222')
    }
    expect(screen.getByLabelText('Điểm đón')).toHaveValue('Đà Nẵng')
    expect(screen.getByLabelText('Điểm trả')).toHaveValue('Huế')
  })

  it('ô đón không có điểm đến, ô trả không có điểm đi', () => {
    renderForm()

    expect(options('Điểm đón')).toEqual(['Đà Nẵng', 'Lăng Cô'])
    expect(options('Điểm trả')).toEqual(['Lăng Cô', 'Huế'])
  })

  it('không sửa gì: không gửi hành khách nào, chỉ gửi điểm đón/trả', async () => {
    fetchMock.mockResolvedValue(jsonResponse(200, SAVED_BOOKING))
    renderForm()

    submit()

    await vi.waitFor(() => expect(onSaved).toHaveBeenCalledWith(SAVED_BOOKING))
    const [url, init] = fetchMock.mock.calls[0]
    expect(String(url)).toBe('http://api.test/api/v1/bookings/DH00100000/details')
    expect(init?.method).toBe('PUT')
    expect(sentBody()).toEqual({
      hanh_khach: [],
      diem_don: { khu_vuc: 'Đà Nẵng', dia_chi: null },
      diem_tra: { khu_vuc: 'Huế', dia_chi: null },
    })
  })

  it('bỏ tích thì sửa được; ghế còn tích không có trong body gửi lên', async () => {
    fetchMock.mockResolvedValue(jsonResponse(200, SAVED_BOOKING))
    renderForm()

    const a02 = seat('A02')
    fireEvent.click(within(a02).getByRole('checkbox', { name: 'Giống người đặt' }))
    expect(within(a02).getByLabelText('Họ tên')).toBeEnabled()
    fireEvent.change(within(a02).getByLabelText('Họ tên'), { target: { value: '  Lê Văn Cường ' } })
    fireEvent.change(within(a02).getByLabelText('Số điện thoại'), { target: { value: '0911222333' } })
    fireEvent.change(screen.getByLabelText('Điểm đón'), { target: { value: 'Lăng Cô' } })
    fireEvent.change(screen.getByLabelText('Địa chỉ cụ thể (không bắt buộc)', { selector: '#diem-don-dia-chi' }), {
      target: { value: ' 12 Lê Lợi ' },
    })
    submit()

    await vi.waitFor(() => expect(onSaved).toHaveBeenCalled())
    const body = sentBody()
    expect(body.hanh_khach).toEqual([{ ve_id: 'VE2', ho_ten: 'Lê Văn Cường', so_dien_thoai: '0911222333' }])
    expect(body.hanh_khach.map((p) => p.ve_id)).not.toContain('VE1')
    expect(body.diem_don).toEqual({ khu_vuc: 'Lăng Cô', dia_chi: '12 Lê Lợi' })
  })

  it('kiểm tra phía client: SĐT sai và đón sau trả báo ngay, không gọi backend', () => {
    renderForm()

    const a01 = seat('A01')
    fireEvent.click(within(a01).getByRole('checkbox', { name: 'Giống người đặt' }))
    fireEvent.change(within(a01).getByLabelText('Số điện thoại'), { target: { value: '123' } })
    fireEvent.change(within(a01).getByLabelText('Họ tên'), { target: { value: '  ' } })
    fireEvent.change(screen.getByLabelText('Điểm đón'), { target: { value: 'Lăng Cô' } })
    fireEvent.change(screen.getByLabelText('Điểm trả'), { target: { value: 'Lăng Cô' } })
    submit()

    expect(within(a01).getByText('Số điện thoại gồm 10 chữ số, bắt đầu bằng 0')).toBeInTheDocument()
    expect(within(a01).getByText('Vui lòng nhập họ tên')).toBeInTheDocument()
    expect(screen.getByText('Điểm đón phải trước điểm trả')).toBeInTheDocument()
    expect(fetchMock).not.toHaveBeenCalled()
  })

  it('lỗi 422 của backend hiện dưới đúng ô của vé đã gửi ở vị trí đó', async () => {
    fetchMock.mockResolvedValue(
      jsonResponse(422, { detail: 'Số điện thoại phải gồm 10 chữ số, bắt đầu bằng 0', truong: 'hanh_khach[0].so_dien_thoai' }),
    )
    renderForm()

    // Chỉ A02 được gửi nên hanh_khach[0] là vé của A02
    const a02 = seat('A02')
    fireEvent.click(within(a02).getByRole('checkbox', { name: 'Giống người đặt' }))
    submit()

    expect(await within(a02).findByText('Số điện thoại phải gồm 10 chữ số, bắt đầu bằng 0')).toBeInTheDocument()
    expect(within(a02).getByLabelText('Số điện thoại')).toHaveAttribute('aria-invalid', 'true')
    expect(within(seat('A01')).queryByText(/Số điện thoại phải/)).not.toBeInTheDocument()
    expect(onSaved).not.toHaveBeenCalled()
  })

  it('lỗi 422 ở địa chỉ hiện dưới ô địa chỉ tương ứng', async () => {
    fetchMock.mockResolvedValue(
      jsonResponse(422, { detail: 'Điểm trả và địa chỉ tối đa 150 ký tự', truong: 'diem_tra.dia_chi' }),
    )
    renderForm()

    submit()

    const field = screen.getByLabelText('Địa chỉ cụ thể (không bắt buộc)', { selector: '#diem-tra-dia-chi' })
    expect(await screen.findByText('Điểm trả và địa chỉ tối đa 150 ký tự')).toBeInTheDocument()
    expect(field).toHaveAttribute('aria-invalid', 'true')
  })

  it('lỗi không có tên trường hiện thành thông báo chung', async () => {
    fetchMock.mockResolvedValue(jsonResponse(400, { detail: 'Đơn đã xác nhận, không thể sửa thông tin', truong: null }))
    renderForm()

    submit()

    expect(await screen.findByRole('alert')).toHaveTextContent('Đơn đã xác nhận, không thể sửa thông tin')
  })

  it('nhận 410 thì báo cho trang', async () => {
    fetchMock.mockResolvedValue(jsonResponse(410, { detail: 'Giữ chỗ đã hết hạn' }))
    renderForm()

    submit()

    await vi.waitFor(() => expect(onGone).toHaveBeenCalled())
    expect(onSaved).not.toHaveBeenCalled()
  })

  describe('đã lưu trước đó', () => {
    const edited: Booking = {
      ...SAVED_BOOKING,
      ve: [
        ticket({ diem_don: 'Lăng Cô – 12 Lê Lợi', diem_tra: 'Huế' }),
        ticket({
          ve_id: 'VE2',
          ghe_id: 'GH2',
          so_ghe: 'A02',
          ho_ten: 'Lê Văn Cường',
          so_dien_thoai: '0911222333',
          diem_don: 'Lăng Cô – 12 Lê Lợi',
          diem_tra: 'Huế',
        }),
      ],
    }

    it('chỉ tích ghế có tên và SĐT trùng tên lúc giữ ghế', () => {
      renderForm(edited)

      expect(within(seat('A01')).getByRole('checkbox', { name: 'Giống người đặt' })).toBeChecked()
      const a02 = seat('A02')
      expect(within(a02).getByRole('checkbox', { name: 'Giống người đặt' })).not.toBeChecked()
      expect(within(a02).getByLabelText('Họ tên')).toHaveValue('Lê Văn Cường')
      expect(screen.getByLabelText('Điểm đón')).toHaveValue('Lăng Cô')
      expect(screen.getByLabelText('Địa chỉ cụ thể (không bắt buộc)', { selector: '#diem-don-dia-chi' })).toHaveValue(
        '12 Lê Lợi',
      )
    })

    it('tích lại ghế đã sửa thì gửi tên, SĐT ghi trên vé lúc giữ ghế', async () => {
      fetchMock.mockResolvedValue(jsonResponse(200, SAVED_BOOKING))
      renderForm(edited)

      const a02 = seat('A02')
      fireEvent.click(within(a02).getByRole('checkbox', { name: 'Giống người đặt' }))
      expect(within(a02).getByLabelText('Họ tên')).toHaveValue('Trần Thị Bình')
      submit()

      await vi.waitFor(() => expect(onSaved).toHaveBeenCalled())
      expect(sentBody().hanh_khach).toEqual([{ ve_id: 'VE2', ho_ten: 'Trần Thị Bình', so_dien_thoai: '0905111222' }])
    })

    it('backend không xác định được tên lúc giữ ghế: so với nguoi_dat, không ghi đè vé bằng tên hồ sơ', async () => {
      fetchMock.mockResolvedValue(jsonResponse(200, SAVED_BOOKING))
      const unknown: Booking = {
        ...edited,
        nguoi_dat: { ho_ten: 'Tên Hồ Sơ', so_dien_thoai: '0905111222', email: null },
        nguoi_dat_luc_giu: null,
      }
      renderForm(unknown)

      const a01 = seat('A01')
      expect(within(a01).getByRole('checkbox', { name: 'Giống người đặt' })).not.toBeChecked()
      fireEvent.click(within(a01).getByRole('checkbox', { name: 'Giống người đặt' }))
      // Vé giữ nguyên tên hiện có, không lấy tên hồ sơ
      expect(within(a01).getByLabelText('Họ tên')).toHaveValue('Trần Thị Bình')
      submit()

      await vi.waitFor(() => expect(onSaved).toHaveBeenCalled())
      expect(sentBody().hanh_khach.map((p) => p.ve_id)).toEqual(['VE2'])
    })
  })
})
