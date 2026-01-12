/**
 * Central design tokens to keep spacing, typography, colors and radii consistent.
 * These mirror the Tailwind CSS variables defined in globals.css so both utility
 * classes and custom components stay in sync.
 */
export const designTokens = {
  colors: {
    background: "hsl(var(--background))",
    foreground: "hsl(var(--foreground))",
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
    success: {
      DEFAULT: "hsl(var(--success))",
      foreground: "hsl(var(--success-foreground))",
    },
    warning: {
      DEFAULT: "hsl(var(--warning))",
      foreground: "hsl(var(--warning-foreground))",
    },
    info: {
      DEFAULT: "hsl(var(--info))",
      foreground: "hsl(var(--info-foreground))",
    },
    border: "hsl(var(--border))",
    input: "hsl(var(--input))",
    ring: "hsl(var(--ring))",
    card: {
      DEFAULT: "hsl(var(--card))",
      foreground: "hsl(var(--card-foreground))",
    },
    popover: {
      DEFAULT: "hsl(var(--popover))",
      foreground: "hsl(var(--popover-foreground))",
    },
    // Terminal/Log colors for ActivityLog and code displays
    terminal: {
      background: "rgb(2, 6, 23)", // slate-950
      backgroundDark: "rgb(0, 0, 0)", // black
      border: "rgb(30, 41, 59)", // slate-800
      text: "rgb(226, 232, 240)", // slate-200
      muted: "rgb(100, 116, 139)", // slate-500
      error: "rgb(248, 113, 113)", // red-400
      warning: "rgb(251, 191, 36)", // amber-400
      info: "rgb(96, 165, 250)", // blue-400
      success: "rgb(74, 222, 128)", // green-400
      debug: "rgb(100, 116, 139)", // slate-500
    },
    // Status-specific colors for consistent state representation
    status: {
      running: {
        border: "hsl(var(--primary) / 0.5)",
        background: "hsl(var(--primary) / 0.05)",
      },
      success: {
        border: "rgb(34, 197, 94, 0.3)", // green-500/30
        background: "rgb(34, 197, 94, 0.05)", // green-500/5
      },
      failed: {
        border: "rgb(239, 68, 68, 0.3)", // red-500/30
        background: "rgb(239, 68, 68, 0.05)", // red-500/5
      },
    },
  },
  typography: {
    fontFamily: {
      sans: "var(--font-inter, 'Inter', system-ui, -apple-system, sans-serif)",
      display: "var(--font-display, var(--font-inter, 'Inter', system-ui, sans-serif))",
      mono: "var(--font-mono, 'Fira Code', 'Courier New', monospace)",
    },
    display: {
      "4xl": {
        fontSize: "2.5rem",
        lineHeight: 1.2,
        fontWeight: 700,
        letterSpacing: "-0.02em",
      },
      "3xl": {
        fontSize: "2rem",
        lineHeight: 1.25,
        fontWeight: 700,
        letterSpacing: "-0.01em",
      },
      "2xl": {
        fontSize: "1.75rem",
        lineHeight: 1.3,
        fontWeight: 600,
      },
      xl: {
        fontSize: "1.5rem",
        lineHeight: 1.35,
        fontWeight: 600,
      },
    },
    heading: {
      h1: {
        fontSize: "2rem",
        lineHeight: 1.3,
        fontWeight: 600,
        letterSpacing: "-0.01em",
      },
      h2: {
        fontSize: "1.5rem",
        lineHeight: 1.35,
        fontWeight: 600,
      },
      h3: {
        fontSize: "1.25rem",
        lineHeight: 1.4,
        fontWeight: 600,
      },
      h4: {
        fontSize: "1.125rem",
        lineHeight: 1.45,
        fontWeight: 600,
      },
      h5: {
        fontSize: "1rem",
        lineHeight: 1.5,
        fontWeight: 600,
      },
      h6: {
        fontSize: "0.875rem",
        lineHeight: 1.5,
        fontWeight: 600,
      },
    },
    body: {
      lg: {
        fontSize: "1.125rem",
        lineHeight: 1.6,
        fontWeight: 400,
      },
      base: {
        fontSize: "1rem",
        lineHeight: 1.5,
        fontWeight: 400,
      },
      sm: {
        fontSize: "0.875rem",
        lineHeight: 1.5,
        fontWeight: 400,
      },
    },
    caption: {
      base: {
        fontSize: "0.875rem",
        lineHeight: 1.4,
        fontWeight: 400,
      },
      sm: {
        fontSize: "0.75rem",
        lineHeight: 1.4,
        fontWeight: 400,
      },
    },
    overline: {
      fontSize: "0.75rem",
      lineHeight: 1.4,
      fontWeight: 600,
      letterSpacing: "0.05em",
      textTransform: "uppercase" as const,
    },
    sizes: {
      xs: "0.75rem",
      sm: "0.875rem",
      base: "1rem",
      lg: "1.125rem",
      xl: "1.25rem",
      "2xl": "1.5rem",
      "3xl": "1.875rem",
      "4xl": "2.25rem",
      "5xl": "3rem",
    },
    lineHeights: {
      tight: 1.25,
      snug: 1.35,
      normal: 1.5,
      relaxed: 1.7,
      loose: 2,
    },
    fontWeights: {
      light: 300,
      normal: 400,
      medium: 500,
      semibold: 600,
      bold: 700,
    },
  },
  spacing: {
    0: "0",
    1: "0.25rem",
    2: "0.5rem",
    3: "0.75rem",
    4: "1rem",
    5: "1.25rem",
    6: "1.5rem",
    8: "2rem",
    10: "2.5rem",
    12: "3rem",
    16: "4rem",
    20: "5rem",
    24: "6rem",
    32: "8rem",
    40: "10rem",
    48: "12rem",
    64: "16rem",
    xs: "0.25rem",
    sm: "0.5rem",
    md: "0.75rem",
    lg: "1rem",
    xl: "1.5rem",
    "2xl": "2rem",
    "3xl": "3rem",
    "4xl": "4rem",
  },
  radii: {
    none: "0",
    sm: "calc(var(--radius) - 4px)",
    md: "calc(var(--radius) - 2px)",
    lg: "var(--radius)",
    xl: "calc(var(--radius) + 2px)",
    "2xl": "calc(var(--radius) + 4px)",
    full: "9999px",
  },
  shadows: {
    xs: "0 1px 2px 0 rgb(0 0 0 / 0.05)",
    sm: "0 1px 2px 0 rgb(0 0 0 / 0.05)",
    md: "0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1)",
    lg: "0 10px 15px -3px rgb(0 0 0 / 0.1), 0 4px 6px -4px rgb(0 0 0 / 0.1)",
    xl: "0 20px 25px -5px rgb(0 0 0 / 0.1), 0 8px 10px -6px rgb(0 0 0 / 0.1)",
    "2xl": "0 25px 50px -12px rgb(0 0 0 / 0.25)",
    inner: "inset 0 2px 4px 0 rgb(0 0 0 / 0.05)",
    none: "none",
  },
  effects: {
    blur: {
      sm: "4px",
      md: "8px",
      lg: "12px",
      xl: "16px",
      "2xl": "24px",
      "3xl": "40px",
    },
    opacity: {
      0: "0",
      5: "0.05",
      10: "0.1",
      20: "0.2",
      25: "0.25",
      30: "0.3",
      40: "0.4",
      50: "0.5",
      60: "0.6",
      70: "0.7",
      75: "0.75",
      80: "0.8",
      90: "0.9",
      95: "0.95",
      100: "1",
    },
  },
  zIndex: {
    hide: "-1",
    base: "0",
    docked: "10",
    dropdown: "1000",
    sticky: "1100",
    banner: "1200",
    overlay: "1300",
    modal: "1400",
    popover: "1500",
    skipLink: "1600",
    tooltip: "1700",
  },
  breakpoints: {
    xs: "0px",
    sm: "640px",
    md: "768px",
    lg: "1024px",
    xl: "1280px",
    "2xl": "1536px",
  },
  transitions: {
    fast: "150ms ease-in-out",
    base: "200ms ease-in-out",
    slow: "300ms ease-in-out",
    slower: "500ms ease-in-out",
  },
} as const;

export type DesignTokens = typeof designTokens;
