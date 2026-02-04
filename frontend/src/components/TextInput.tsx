export function TextInput({ 
  className = "", 
  error = false,
  ...props 
}: { 
  className?: string;
  error?: boolean;
} & React.InputHTMLAttributes<HTMLInputElement>) {
  return (
    <div className="focus-underline">
      <input
        className={`
          w-full 
          border-2 border-black 
          px-3 py-2 
          text-sm 
          rounded-md 
          bg-white
          transition-all duration-base ease-standard
          focus:outline-none 
          focus:border-accent-amber
          placeholder:text-muted
          ${error ? 'border-accent-orange animate-error-flash' : ''}
          ${className}
        `}
        {...props}
      />
    </div>
  )
}
