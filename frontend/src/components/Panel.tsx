export function Panel({ 
  children, 
  className = "",
  accent = false 
}: { 
  children: React.ReactNode; 
  className?: string;
  accent?: boolean;
}) {
  return (
    <div className={`
      bg-white 
      border-2 border-black 
      rounded-md 
      p-6 
      transition-all duration-base ease-standard
      ${accent ? 'relative' : ''}
      ${className}
    `}>
      {accent && (
        <div className="absolute top-0 left-0 w-full h-1 bg-accent-yellow accent-bar-reveal"></div>
      )}
      {children}
    </div>
  )
}
