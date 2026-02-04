import type { Config } from "tailwindcss";

export default {
  content: ["./pages/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}", "./app/**/*.{ts,tsx}", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        black: '#0B0B0B',
        white: '#FFFFFF',
        paper: '#faf4d6ff',
        border: '#1F1F1F',
        muted: '#6B6B6B',
        'accent-yellow': '#ffd45e',
        'accent-amber': '#F2A541',
        'accent-orange': '#E36414'
      },
      fontFamily: {
        sans: ['IBM Plex Sans', 'Inter', 'system-ui'],
        heading: ['Space Grotesk', 'IBM Plex Sans'],
        mono: ['JetBrains Mono', 'monospace']
      },
      borderWidth: {
        DEFAULT: '1.5px'
      },
      borderRadius: {
        DEFAULT: '6px',
        md: '8px',
        lg: '12px'
      },
      spacing: {
        '18': '4.5rem',
        '88': '22rem',
        '128': '32rem'
      },
      maxWidth: {
        '7xl': '80rem',
        '8xl': '88rem'
      },
      transitionDuration: {
        'fast': '100ms',
        'base': '140ms',
        'slow': '180ms'
      },
      transitionTimingFunction: {
        'standard': 'cubic-bezier(0.2, 0, 0, 1)'
      },
      animation: {
        'page-enter': 'pageEnter 160ms standard',
        'section-enter': 'sectionEnter 140ms standard',
        'accent-bar-slide': 'accentBarSlide 140ms standard',
        'accent-bar-reveal': 'accentBarReveal 180ms standard',
        'progress-rule': 'progressRule 2s standard infinite',
        'logo-stamp': 'logoStamp 120ms standard',
        'error-flash': 'errorFlash 120ms standard'
      },
      keyframes: {
        pageEnter: {
          from: { opacity: '0', transform: 'translateY(4px)' },
          to: { opacity: '1', transform: 'translateY(0)' }
        },
        sectionEnter: {
          from: { opacity: '0', transform: 'translateY(6px)' },
          to: { opacity: '1', transform: 'translateY(0)' }
        },
        accentBarSlide: {
          from: { transform: 'translateX(-100%)' },
          to: { transform: 'translateX(0)' }
        },
        accentBarReveal: {
          from: { width: '0%' },
          to: { width: '100%' }
        },
        progressRule: {
          '0%': { transform: 'translateX(-100%)' },
          '50%': { transform: 'translateX(0%)' },
          '100%': { transform: 'translateX(100%)' }
        },
        logoStamp: {
          from: { opacity: '0', transform: 'scale(0.92)' },
          to: { opacity: '1', transform: 'scale(1)' }
        },
        errorFlash: {
          '0%, 100%': { borderColor: '#E36414' },
          '50%': { borderColor: '#E36414', backgroundColor: 'rgba(227, 100, 20, 0.1)' }
        }
      }
    },
  },
  plugins: [],
} satisfies Config;
