export function ControlButton({
  variant = "secondary",
  children,
  className = "",
  loading = false,
  ...props
}: {
  variant?: "primary" | "secondary" | "destructive"
  children: React.ReactNode
  className?: string
  loading?: boolean
} & React.ButtonHTMLAttributes<HTMLButtonElement>) {
  const base = "border-2 border-black px-4 py-2 text-sm font-medium rounded-md transition-all duration-base ease-standard btn-active relative overflow-hidden"

  const styles = {
    primary: "bg-accent-orange text-black hover:bg-accent-amber",
    secondary: "bg-white text-black hover:bg-accent-yellow",
    destructive: "bg-white text-black hover:bg-accent-orange"
  }

  return (
    <button 
      className={`${base} ${styles[variant]} ${className} ${loading ? 'cursor-not-allowed opacity-60' : ''}`} 
      disabled={loading}
      {...props}
    >
      {loading && (
        <div className="absolute inset-0 flex items-center justify-center">
          <div className="w-full h-1 bg-accent-orange/30 rounded-full overflow-hidden">
            <div className="h-full bg-accent-orange animate-progress-rule"></div>
          </div>
        </div>
      )}
      <span className={loading ? 'opacity-0' : ''}>{children}</span>
    </button>
  )
}
