import logoUrl from '../assets/logo-web.png'

type Props = {
  className?: string
}

/**
 * Logo nhà xe (bản thu nhỏ của src/assets/logo.png). Ảnh có nền trắng, nên đặt trên nền
 * màu thì bọc trong khung trắng. Tên nhà xe luôn hiện bằng chữ cạnh logo, nên ảnh chỉ để
 * trang trí (alt rỗng), trình đọc màn hình không đọc lặp tên.
 */
export default function BrandLogo({ className = 'h-24 w-24' }: Props) {
  return <img src={logoUrl} alt="" data-testid="brand-logo" className={`shrink-0 object-contain ${className}`} />
}
