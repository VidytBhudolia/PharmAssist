/** @type {import('tailwindcss').Config} */
export default {
  darkMode: ["class"],
  content: ["./index.html", "./src/**/*.{js,jsx,ts,tsx}"],
  theme: {
    extend: {
      /* ═══════════════════════════════════════════════════════════════════════════
         TYPOGRAPHY SCALE - Enterprise Dashboard / Technical Reading
         Inspired by: Palantir Foundry, Notion Enterprise, Vercel
         ═══════════════════════════════════════════════════════════════════════════ */
      fontFamily: {
        sans: [
          "DM Sans",
          "Plus Jakarta Sans",
          "-apple-system",
          "BlinkMacSystemFont",
          "Segoe UI",
          "sans-serif",
        ],
        mono: ["JetBrains Mono", "SF Mono", "Fira Code", "Monaco", "Consolas", "monospace"],
        display: ["Plus Jakarta Sans", "DM Sans", "-apple-system", "sans-serif"],
      },
      fontSize: {
        /* Micro - Labels, badges, captions */
        "2xs": ["0.625rem", { lineHeight: "0.875rem", letterSpacing: "0.02em" }], // 10px
        xs: ["0.6875rem", { lineHeight: "1rem", letterSpacing: "0.01em" }], // 11px
        /* Body - Primary reading */
        sm: ["0.75rem", { lineHeight: "1.125rem", letterSpacing: "0.005em" }], // 12px
        base: ["0.8125rem", { lineHeight: "1.25rem", letterSpacing: "0" }], // 13px
        md: ["0.875rem", { lineHeight: "1.375rem", letterSpacing: "0" }], // 14px
        /* Headings - Dense dashboard headers */
        lg: ["0.9375rem", { lineHeight: "1.5rem", letterSpacing: "-0.01em" }], // 15px
        xl: ["1.0625rem", { lineHeight: "1.625rem", letterSpacing: "-0.015em" }], // 17px
        "2xl": ["1.25rem", { lineHeight: "1.75rem", letterSpacing: "-0.02em" }], // 20px
        "3xl": ["1.5rem", { lineHeight: "2rem", letterSpacing: "-0.025em" }], // 24px
        "4xl": ["1.875rem", { lineHeight: "2.25rem", letterSpacing: "-0.03em" }], // 30px
        /* Display - Hero, empty states */
        "5xl": ["2.25rem", { lineHeight: "2.5rem", letterSpacing: "-0.035em" }], // 36px
      },

      /* ═══════════════════════════════════════════════════════════════════════════
         SPACING SYSTEM - 4pt/8pt Grid
         Consistent, dense layouts for data-heavy interfaces
         ═══════════════════════════════════════════════════════════════════════════ */
      spacing: {
        px: "1px",
        0: "0",
        0.5: "0.125rem", // 2px
        1: "0.25rem", // 4px - base unit
        1.5: "0.375rem", // 6px
        2: "0.5rem", // 8px - base unit
        2.5: "0.625rem", // 10px
        3: "0.75rem", // 12px
        3.5: "0.875rem", // 14px
        4: "1rem", // 16px
        5: "1.25rem", // 20px
        6: "1.5rem", // 24px
        7: "1.75rem", // 28px
        8: "2rem", // 32px
        9: "2.25rem", // 36px
        10: "2.5rem", // 40px
        11: "2.75rem", // 44px
        12: "3rem", // 48px
        14: "3.5rem", // 56px
        16: "4rem", // 64px
        18: "4.5rem", // 72px
        20: "5rem", // 80px
        24: "6rem", // 96px
        28: "7rem", // 112px
        32: "8rem", // 128px
        36: "9rem", // 144px
        40: "10rem", // 160px
        44: "11rem", // 176px
        48: "12rem", // 192px
        52: "13rem", // 208px
        56: "14rem", // 224px
        60: "15rem", // 240px
        64: "16rem", // 256px
        72: "18rem", // 288px
        80: "20rem", // 320px
        96: "24rem", // 384px
      },

      /* ═══════════════════════════════════════════════════════════════════════════
         BORDER RADIUS - Subtle, clinical aesthetic
         ═══════════════════════════════════════════════════════════════════════════ */
      borderRadius: {
        none: "0",
        xs: "0.125rem", // 2px - Tags, micro elements
        sm: "0.1875rem", // 3px - Inputs, buttons
        DEFAULT: "0.25rem", // 4px - Cards, containers
        md: "0.375rem", // 6px - Modals, panels
        lg: "0.5rem", // 8px - Large cards
        xl: "0.75rem", // 12px - Hero sections
        "2xl": "1rem", // 16px - Feature cards
        full: "9999px", // Pills, avatars
      },

      /* ═══════════════════════════════════════════════════════════════════════════
         SEMANTIC COLOR SYSTEM - Clinical / Research Environments
         Pharma-grade: Precise, trustworthy, accessible
         ═══════════════════════════════════════════════════════════════════════════ */
      colors: {
        /* Base semantic colors (CSS variable driven for theme switching) */
        background: "hsl(var(--background))",
        foreground: "hsl(var(--foreground))",
        card: {
          DEFAULT: "hsl(var(--card))",
          foreground: "hsl(var(--card-foreground))",
        },
        popover: {
          DEFAULT: "hsl(var(--popover))",
          foreground: "hsl(var(--popover-foreground))",
        },
        primary: {
          DEFAULT: "hsl(var(--primary))",
          foreground: "hsl(var(--primary-foreground))",
        },
        secondary: {
          DEFAULT: "hsl(var(--secondary))",
          foreground: "hsl(var(--secondary-foreground))",
        },
        muted: {
          DEFAULT: "hsl(var(--muted))",
          foreground: "hsl(var(--muted-foreground))",
        },
        accent: {
          DEFAULT: "hsl(var(--accent))",
          foreground: "hsl(var(--accent-foreground))",
        },
        destructive: {
          DEFAULT: "hsl(var(--destructive))",
          foreground: "hsl(var(--destructive-foreground))",
        },
        border: "hsl(var(--border))",
        input: "hsl(var(--input))",
        ring: "hsl(var(--ring))",

        /* ─────────────────────────────────────────────────────────────────────────
           CLINICAL COLOR PALETTE
           Purpose-driven colors for pharmaceutical/biotech interfaces
           ───────────────────────────────────────────────────────────────────────── */

        /* Slate - Primary neutral (Palantir-inspired) */
        slate: {
          50: "#f8fafc",
          100: "#f1f5f9",
          150: "#e9eef4",
          200: "#e2e8f0",
          300: "#cbd5e1",
          400: "#94a3b8",
          500: "#64748b",
          600: "#475569",
          700: "#334155",
          800: "#1e293b",
          850: "#172033",
          900: "#0f172a",
          925: "#0c1322",
          950: "#020617",
        },

        /* Clinical Blue - Trust, precision, data (Benchling-inspired) */
        clinical: {
          50: "#eff6ff",
          100: "#dbeafe",
          200: "#bfdbfe",
          300: "#93c5fd",
          400: "#60a5fa",
          500: "#3b82f6",
          600: "#2563eb",
          700: "#1d4ed8",
          800: "#1e40af",
          900: "#1e3a8a",
          950: "#172554",
        },

        /* Teal - Success, positive outcomes, growth */
        success: {
          50: "#f0fdfa",
          100: "#ccfbf1",
          200: "#99f6e4",
          300: "#5eead4",
          400: "#2dd4bf",
          500: "#14b8a6",
          600: "#0d9488",
          700: "#0f766e",
          800: "#115e59",
          900: "#134e4a",
          950: "#042f2e",
        },

        /* Amber - Warnings, attention, pending */
        warning: {
          50: "#fffbeb",
          100: "#fef3c7",
          200: "#fde68a",
          300: "#fcd34d",
          400: "#fbbf24",
          500: "#f59e0b",
          600: "#d97706",
          700: "#b45309",
          800: "#92400e",
          900: "#78350f",
          950: "#451a03",
        },

        /* Rose - Errors, critical alerts, destructive */
        danger: {
          50: "#fff1f2",
          100: "#ffe4e6",
          200: "#fecdd3",
          300: "#fda4af",
          400: "#fb7185",
          500: "#f43f5e",
          600: "#e11d48",
          700: "#be123c",
          800: "#9f1239",
          900: "#881337",
          950: "#4c0519",
        },

        /* Violet - Insights, AI, intelligence */
        insight: {
          50: "#f5f3ff",
          100: "#ede9fe",
          200: "#ddd6fe",
          300: "#c4b5fd",
          400: "#a78bfa",
          500: "#8b5cf6",
          600: "#7c3aed",
          700: "#6d28d9",
          800: "#5b21b6",
          900: "#4c1d95",
          950: "#2e1065",
        },

        /* Emerald - Clinical trials, research positive */
        research: {
          50: "#ecfdf5",
          100: "#d1fae5",
          200: "#a7f3d0",
          300: "#6ee7b7",
          400: "#34d399",
          500: "#10b981",
          600: "#059669",
          700: "#047857",
          800: "#065f46",
          900: "#064e3b",
          950: "#022c22",
        },

        /* Cyan - Data, analytics, metrics */
        data: {
          50: "#ecfeff",
          100: "#cffafe",
          200: "#a5f3fc",
          300: "#67e8f9",
          400: "#22d3ee",
          500: "#06b6d4",
          600: "#0891b2",
          700: "#0e7490",
          800: "#155e75",
          900: "#164e63",
          950: "#083344",
        },

        /* Chart colors - Data visualization palette */
        chart: {
          1: "hsl(var(--chart-1))",
          2: "hsl(var(--chart-2))",
          3: "hsl(var(--chart-3))",
          4: "hsl(var(--chart-4))",
          5: "hsl(var(--chart-5))",
          6: "hsl(var(--chart-6))",
          7: "hsl(var(--chart-7))",
          8: "hsl(var(--chart-8))",
        },

        /* Panel/Surface colors */
        surface: {
          DEFAULT: "hsl(var(--surface))",
          raised: "hsl(var(--surface-raised))",
          overlay: "hsl(var(--surface-overlay))",
          sunken: "hsl(var(--surface-sunken))",
        },
      },

      /* ═══════════════════════════════════════════════════════════════════════════
         BOX SHADOWS - Subtle depth for clinical interfaces
         ═══════════════════════════════════════════════════════════════════════════ */
      boxShadow: {
        none: "none",
        xs: "0 1px 2px 0 rgb(0 0 0 / 0.03)",
        sm: "0 1px 3px 0 rgb(0 0 0 / 0.04), 0 1px 2px -1px rgb(0 0 0 / 0.04)",
        DEFAULT: "0 2px 4px -1px rgb(0 0 0 / 0.05), 0 1px 2px -1px rgb(0 0 0 / 0.03)",
        md: "0 4px 6px -1px rgb(0 0 0 / 0.05), 0 2px 4px -2px rgb(0 0 0 / 0.03)",
        lg: "0 10px 15px -3px rgb(0 0 0 / 0.05), 0 4px 6px -4px rgb(0 0 0 / 0.03)",
        xl: "0 20px 25px -5px rgb(0 0 0 / 0.05), 0 8px 10px -6px rgb(0 0 0 / 0.03)",
        "2xl": "0 25px 50px -12px rgb(0 0 0 / 0.15)",
        inner: "inset 0 2px 4px 0 rgb(0 0 0 / 0.03)",
        /* Dark mode shadows */
        "dark-xs": "0 1px 2px 0 rgb(0 0 0 / 0.2)",
        "dark-sm": "0 1px 3px 0 rgb(0 0 0 / 0.3), 0 1px 2px -1px rgb(0 0 0 / 0.2)",
        "dark-md": "0 4px 6px -1px rgb(0 0 0 / 0.4), 0 2px 4px -2px rgb(0 0 0 / 0.3)",
        "dark-lg": "0 10px 15px -3px rgb(0 0 0 / 0.5), 0 4px 6px -4px rgb(0 0 0 / 0.4)",
        /* Glow effects for focus states */
        "glow-sm": "0 0 0 2px hsl(var(--primary) / 0.15)",
        "glow-md": "0 0 0 3px hsl(var(--primary) / 0.2)",
        "glow-clinical": "0 0 0 3px hsl(217 91% 60% / 0.2)",
        "glow-success": "0 0 0 3px hsl(168 76% 42% / 0.2)",
        "glow-danger": "0 0 0 3px hsl(347 77% 50% / 0.2)",
      },

      /* ═══════════════════════════════════════════════════════════════════════════
         TRANSITIONS & ANIMATIONS - Smooth, professional
         ═══════════════════════════════════════════════════════════════════════════ */
      transitionDuration: {
        75: "75ms",
        100: "100ms",
        150: "150ms",
        200: "200ms",
        250: "250ms",
        300: "300ms",
        400: "400ms",
        500: "500ms",
      },
      transitionTimingFunction: {
        DEFAULT: "cubic-bezier(0.4, 0, 0.2, 1)",
        linear: "linear",
        in: "cubic-bezier(0.4, 0, 1, 1)",
        out: "cubic-bezier(0, 0, 0.2, 1)",
        "in-out": "cubic-bezier(0.4, 0, 0.2, 1)",
        bounce: "cubic-bezier(0.68, -0.55, 0.265, 1.55)",
      },
      keyframes: {
        "fade-in": {
          "0%": { opacity: "0" },
          "100%": { opacity: "1" },
        },
        "fade-out": {
          "0%": { opacity: "1" },
          "100%": { opacity: "0" },
        },
        "slide-in-up": {
          "0%": { transform: "translateY(8px)", opacity: "0" },
          "100%": { transform: "translateY(0)", opacity: "1" },
        },
        "slide-in-down": {
          "0%": { transform: "translateY(-8px)", opacity: "0" },
          "100%": { transform: "translateY(0)", opacity: "1" },
        },
        "scale-in": {
          "0%": { transform: "scale(0.96)", opacity: "0" },
          "100%": { transform: "scale(1)", opacity: "1" },
        },
        shimmer: {
          "0%": { backgroundPosition: "-200% 0" },
          "100%": { backgroundPosition: "200% 0" },
        },
        pulse: {
          "0%, 100%": { opacity: "1" },
          "50%": { opacity: "0.5" },
        },
        "spin-slow": {
          "0%": { transform: "rotate(0deg)" },
          "100%": { transform: "rotate(360deg)" },
        },
      },
      animation: {
        "fade-in": "fade-in 0.2s ease-out",
        "fade-out": "fade-out 0.15s ease-in",
        "slide-in-up": "slide-in-up 0.2s ease-out",
        "slide-in-down": "slide-in-down 0.2s ease-out",
        "scale-in": "scale-in 0.2s ease-out",
        shimmer: "shimmer 2s infinite linear",
        "pulse-slow": "pulse 2s ease-in-out infinite",
        "spin-slow": "spin-slow 8s linear infinite",
      },

      /* ═══════════════════════════════════════════════════════════════════════════
         ADDITIONAL UTILITIES
         ═══════════════════════════════════════════════════════════════════════════ */
      backdropBlur: {
        xs: "2px",
        sm: "4px",
        DEFAULT: "8px",
        md: "12px",
        lg: "16px",
        xl: "24px",
      },
      opacity: {
        2.5: "0.025",
        3.5: "0.035",
        7.5: "0.075",
        15: "0.15",
        35: "0.35",
        65: "0.65",
        85: "0.85",
      },
      zIndex: {
        1: "1",
        2: "2",
        dropdown: "1000",
        sticky: "1020",
        fixed: "1030",
        backdrop: "1040",
        modal: "1050",
        popover: "1060",
        tooltip: "1070",
        toast: "1080",
      },
    },
  },
  plugins: [require("tailwindcss-animate"), require("tailwind-scrollbar")],
};
