export function SidebarItem({
  active,
  children,
  onClick,
}: {
  active?: boolean
  children: React.ReactNode
  onClick?: () => void
}) {
  return (
    <div
      className={`
        px-3 py-3 text-base font-medium transition-all duration-base ease-standard cursor-pointer relative rounded-md
        ${active
          ? "bg-accent-yellow text-black border-l-4 border-accent-orange"
          : "text-black hover:bg-accent-yellow/40 border-l-4 border-transparent hover:border-accent-orange"
        }
      `}
      onClick={onClick}
    >
      {active && (
        <div className="absolute top-0 left-0 w-1 h-full bg-accent-orange accent-bar-slide"></div>
      )}
      {children}
    </div>
  )
}
