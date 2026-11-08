import { act, fireEvent, render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'

import InlineConfirm from './InlineConfirm'

describe('InlineConfirm', () => {
  it('hiện tiêu đề, nội dung; bấm "Quay lại" gọi onCancel', () => {
    const onCancel = vi.fn()
    render(
      <InlineConfirm title="Xác nhận" onConfirm={vi.fn()} onCancel={onCancel}>
        Nội dung xác nhận
      </InlineConfirm>,
    )

    expect(screen.getByRole('alertdialog', { name: 'Xác nhận' })).toHaveTextContent('Nội dung xác nhận')
    fireEvent.click(screen.getByRole('button', { name: 'Quay lại' }))
    expect(onCancel).toHaveBeenCalledOnce()
  })

  it('đang gửi thì khóa nút, bấm hai lần chỉ gọi onConfirm một lần', async () => {
    let finish: () => void = () => {}
    const onConfirm = vi.fn(() => new Promise<void>((resolve) => (finish = resolve)))
    render(
      <InlineConfirm title="Xác nhận" confirmLabel="Đồng ý" onConfirm={onConfirm} onCancel={vi.fn()}>
        x
      </InlineConfirm>,
    )

    const button = screen.getByRole('button', { name: 'Đồng ý' })
    fireEvent.click(button)
    fireEvent.click(button)

    expect(onConfirm).toHaveBeenCalledOnce()
    expect(screen.getByRole('button', { name: 'Đang lưu…' })).toBeDisabled()
    expect(screen.getByRole('button', { name: 'Quay lại' })).toBeDisabled()
    await act(async () => finish())
    expect(screen.getByRole('button', { name: 'Đồng ý' })).toBeEnabled()
  })
})
