// Icon SVG vẽ tay (không dùng thư viện icon); màu theo currentColor.
type IconProps = { className?: string }

function Svg({ className = 'h-5 w-5', children }: IconProps & { children: React.ReactNode }) {
  return (
    <svg
      aria-hidden="true"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={1.8}
      strokeLinecap="round"
      strokeLinejoin="round"
      className={className}
    >
      {children}
    </svg>
  )
}

export function HomeIcon(props: IconProps) {
  return (
    <Svg {...props}>
      <path d="M3 11l9-7 9 7" />
      <path d="M5 10v10h5v-6h4v6h5V10" />
    </Svg>
  )
}

export function SearchIcon(props: IconProps) {
  return (
    <Svg {...props}>
      <circle cx="11" cy="11" r="6.5" />
      <path d="M20 20l-4.2-4.2" />
    </Svg>
  )
}

export function TicketIcon(props: IconProps) {
  return (
    <Svg {...props}>
      <path d="M3 8a2 2 0 0 0 2-2h14a2 2 0 0 0 2 2v2a2 2 0 0 0 0 4v2a2 2 0 0 0-2 2H5a2 2 0 0 0-2-2v-2a2 2 0 0 0 0-4z" />
      <path d="M14 6v12" strokeDasharray="2 2" />
    </Svg>
  )
}

export function LookupIcon(props: IconProps) {
  return (
    <Svg {...props}>
      <rect x="4" y="3" width="13" height="18" rx="2" />
      <path d="M8 8h5M8 12h3" />
      <circle cx="16" cy="16" r="3" />
      <path d="M21 21l-2.8-2.8" />
    </Svg>
  )
}

export function UserIcon(props: IconProps) {
  return (
    <Svg {...props}>
      <circle cx="12" cy="8" r="4" />
      <path d="M4 21a8 8 0 0 1 16 0" />
    </Svg>
  )
}

export function PinIcon(props: IconProps) {
  return (
    <Svg {...props}>
      <path d="M12 21s-6-5.5-6-11a6 6 0 0 1 12 0c0 5.5-6 11-6 11z" />
      <circle cx="12" cy="10" r="2" />
    </Svg>
  )
}

export function SwapIcon(props: IconProps) {
  return (
    <Svg {...props}>
      <path d="M4 8h14l-3-3M20 16H6l3 3" />
    </Svg>
  )
}

export function SteeringWheelIcon(props: IconProps) {
  return (
    <Svg {...props}>
      <circle cx="12" cy="12" r="9" />
      <circle cx="12" cy="12" r="2.5" />
      <path d="M3.5 10.5h6M14.5 10.5h6M12 14.5V21" />
    </Svg>
  )
}

/** Ghế ngồi nhìn từ trên xuống, tô bằng currentColor. */
export function SeatIcon({ className = 'h-9 w-9' }: IconProps) {
  return (
    <svg aria-hidden="true" viewBox="0 0 32 32" className={className} fill="currentColor">
      <rect x="7" y="3" width="18" height="17" rx="4" />
      <rect x="3" y="11" width="4" height="13" rx="2" />
      <rect x="25" y="11" width="4" height="13" rx="2" />
      <rect x="7" y="21" width="18" height="7" rx="2.5" />
    </svg>
  )
}

/** Biểu tượng xe khách dùng làm logo tạm (chưa có file logo). */
export function BusLogo({ className = 'h-10 w-10' }: IconProps) {
  return (
    <svg aria-hidden="true" viewBox="0 0 48 48" className={className}>
      <circle cx="24" cy="24" r="23" fill="#ffffff" />
      <circle cx="24" cy="24" r="20" fill="none" stroke="currentColor" strokeWidth="2" />
      <path
        d="M11 28v-7c0-3 2-5 5-5h14c3 0 5 2 7 5l1 2v5a2 2 0 0 1-2 2H13a2 2 0 0 1-2-2z"
        fill="currentColor"
      />
      <path d="M15 19h6v4h-6zM23 19h6v4h-6z" fill="#ffffff" />
      <path d="M31 19h1.5c1 0 2 1 2.5 2l.6 2H31z" fill="#ffffff" />
      <circle cx="17" cy="30" r="2.6" fill="#ffffff" stroke="currentColor" strokeWidth="1.5" />
      <circle cx="31" cy="30" r="2.6" fill="#ffffff" stroke="currentColor" strokeWidth="1.5" />
      <path d="M10 35c5-2 9 1 14-1s9-1 14 1" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" />
    </svg>
  )
}
