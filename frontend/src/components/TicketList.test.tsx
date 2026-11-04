import { render, screen, within } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

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
})
