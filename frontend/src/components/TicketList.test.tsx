import { fireEvent, render, screen, within } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'

import { ticket } from '../utils/testBookings'
import TicketList from './TicketList'

describe('TicketList', () => {
  it('mỗi vé hiện mã vé, ghế, hành khách, điểm đón/trả, giá và trạng thái theo backend', () => {
    render(
      <TicketList
        tickets={[
          ticket({
            ve_id: 'VE00100001',
            trang_thai_ve: 'DA_XAC_NHAN',
            trang_thai_thanh_toan: 'CHO_THU_TIEN_MAT',
            diem_don: 'Lăng Cô – 12 Lê Lợi',
            diem_tra: 'Huế',
          }),
          ticket({ ve_id: 'VE00100002', so_ghe: 'A02', ho_ten: 'Lê Văn C', trang_thai_thanh_toan: 'DA_THANH_TOAN' }),
        ]}
      />,
    )

    const items = within(screen.getByRole('list', { name: 'Vé điện tử' })).getAllByRole('listitem')
    expect(items).toHaveLength(2)
    const first = screen.getByRole('listitem', { name: 'Vé VE00100001' })
    expect(first).toHaveTextContent('Mã vé: VE00100001')
    expect(first).toHaveTextContent('Ghế A01')
    expect(first).toHaveTextContent('Trần Thị Bình')
    expect(first).toHaveTextContent('Lăng Cô – 12 Lê Lợi')
    expect(first).toHaveTextContent('Huế')
    expect(first).toHaveTextContent('200.000 đ')
    expect(first).toHaveTextContent('Chờ thu tiền mặt')
    expect(screen.getByRole('listitem', { name: 'Vé VE00100002' })).toHaveTextContent('Đã thanh toán')
  })

  it('nút "Hủy vé" chỉ hiện với vé đã xác nhận khi có onCancel; bấm gọi đúng vé', () => {
    const onCancel = vi.fn()
    const confirmed = ticket({ ve_id: 'VE00100001', trang_thai_ve: 'DA_XAC_NHAN' })
    render(<TicketList tickets={[confirmed, ticket({ ve_id: 'VE00100002', trang_thai_ve: 'DA_HUY' })]} onCancel={onCancel} />)

    const buttons = screen.getAllByRole('button', { name: 'Hủy vé' })
    expect(buttons).toHaveLength(1)
    expect(within(screen.getByRole('listitem', { name: 'Vé VE00100001' })).getByRole('button', { name: 'Hủy vé' })).toBe(
      buttons[0],
    )
    expect(screen.queryByRole('button', { name: 'Đổi vé' })).not.toBeInTheDocument()
    fireEvent.click(buttons[0])
    expect(onCancel).toHaveBeenCalledWith(confirmed)
  })

  it('không truyền onCancel: không có nút "Hủy vé"', () => {
    render(<TicketList tickets={[ticket({ trang_thai_ve: 'DA_XAC_NHAN' })]} />)

    expect(screen.queryByRole('button', { name: 'Hủy vé' })).not.toBeInTheDocument()
  })
})
