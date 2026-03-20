/** @type {import('tailwindcss').Config} */
module.exports = {
    darkMode: ["class"],
    content: [
        "./src/**/*.{js,jsx,ts,tsx}",
        "./public/index.html"
    ],
    theme: {
        extend: {
            fontFamily: {
                heading: ['"DM Serif Display"', 'serif'],
                body: ['"Inter"', 'sans-serif'],
            },
            colors: {
                /* ── Official Brand Palette ── */
                'foiled-gold': '#D4A828',
                'champagne': '#E8CA5A',
                'gold-wash': '#F0E6C8',
                'deep-ink': '#1E2A3A',
                'navy-hover': '#2A3B50',
                'warm-cream': '#FFFBF2',
                'forest': '#2D6A4F',
                'wheat': '#E5DBC8',
                'parchment': '#F3EBE0',
                'merlot': '#9B2C2C',
                'slate-ink': '#3A4D63',
                'pewter': '#7A8694',
                /* ── Legacy aliases → remapped to brand ── */
                'honey': '#D4A828',
                'honey-soft': '#E8CA5A',
                'honey-cream': '#FFFBF2',
                'honey-amber': '#D4A828',
                'honey-dark': '#2A3B50',
                'vinyl-black': '#1E2A3A',
                'honey-muted': '#F0E6C8',
                background: 'hsl(var(--background))',
                foreground: 'hsl(var(--foreground))',
                card: {
                    DEFAULT: 'hsl(var(--card))',
                    foreground: 'hsl(var(--card-foreground))'
                },
                popover: {
                    DEFAULT: 'hsl(var(--popover))',
                    foreground: 'hsl(var(--popover-foreground))'
                },
                primary: {
                    DEFAULT: 'hsl(var(--primary))',
                    foreground: 'hsl(var(--primary-foreground))'
                },
                secondary: {
                    DEFAULT: 'hsl(var(--secondary))',
                    foreground: 'hsl(var(--secondary-foreground))'
                },
                muted: {
                    DEFAULT: 'hsl(var(--muted))',
                    foreground: 'hsl(var(--muted-foreground))'
                },
                accent: {
                    DEFAULT: 'hsl(var(--accent))',
                    foreground: 'hsl(var(--accent-foreground))'
                },
                destructive: {
                    DEFAULT: 'hsl(var(--destructive))',
                    foreground: 'hsl(var(--destructive-foreground))'
                },
                border: 'hsl(var(--border))',
                input: 'hsl(var(--input))',
                ring: 'hsl(var(--ring))',
                chart: {
                    '1': 'hsl(var(--chart-1))',
                    '2': 'hsl(var(--chart-2))',
                    '3': 'hsl(var(--chart-3))',
                    '4': 'hsl(var(--chart-4))',
                    '5': 'hsl(var(--chart-5))'
                }
            },
            borderRadius: {
                lg: 'var(--radius)',
                md: 'calc(var(--radius) - 2px)',
                sm: 'calc(var(--radius) - 4px)',
                xl: '1rem',
                '2xl': '1.5rem',
            },
            keyframes: {
                'accordion-down': {
                    from: { height: '0' },
                    to: { height: 'var(--radix-accordion-content-height)' }
                },
                'accordion-up': {
                    from: { height: 'var(--radix-accordion-content-height)' },
                    to: { height: '0' }
                },
                'spin-slow': {
                    from: { transform: 'rotate(0deg)' },
                    to: { transform: 'rotate(360deg)' }
                },
                'fade-in': {
                    from: { opacity: '0' },
                    to: { opacity: '1' }
                },
                'slide-up': {
                    from: { opacity: '0', transform: 'translateY(10px)' },
                    to: { opacity: '1', transform: 'translateY(0)' }
                },
                'buzz': {
                    '0%, 100%': { transform: 'translateX(0)' },
                    '25%': { transform: 'translateX(-2px)' },
                    '75%': { transform: 'translateX(2px)' }
                },
                'float': {
                    '0%, 100%': { transform: 'translateY(0)' },
                    '50%': { transform: 'translateY(-5px)' }
                }
            },
            animation: {
                'accordion-down': 'accordion-down 0.2s ease-out',
                'accordion-up': 'accordion-up 0.2s ease-out',
                'spin-slow': 'spin-slow 8s linear infinite',
                'fade-in': 'fade-in 0.5s ease-out',
                'slide-up': 'slide-up 0.7s ease-out',
                'buzz': 'buzz 0.3s ease-in-out',
                'float': 'float 3s ease-in-out infinite'
            },
            boxShadow: {
                'gold-primary': '0 2px 4px #D4A82828, 0 4px 12px #D4A82820',
                'gold-cta': '0 2px 4px #D4A82828, 0 4px 12px #D4A82820, inset 0 1px 0 rgba(255,255,255,0.2)',
                'navy-accent': '0 2px 4px #1E2A3A20, 0 4px 12px #1E2A3A12',
                'card': '0 1px 3px rgba(30,42,58,0.04), 0 4px 12px rgba(30,42,58,0.06)',
                'card-hover': '0 2px 8px rgba(30,42,58,0.07), 0 8px 24px rgba(30,42,58,0.10)',
                'gold-badge': '0 2px 6px #D4A82830',
                'navy-badge': '0 2px 6px #1E2A3A25',
                /* Legacy */
                'honey': '0 2px 4px #D4A82828, 0 4px 12px #D4A82820',
                'vinyl': '0 10px 30px -5px rgba(0, 0, 0, 0.3)',
                'float': '0 20px 40px -5px rgba(30,42,58,0.15)',
            }
        }
    },
    plugins: [require("tailwindcss-animate")],
};
