"use client";

import * as React from "react";

type Theme = "light" | "dark";

type ThemeProviderProps = {
  children: React.ReactNode;
  defaultTheme?: Theme;
  storageKey?: string;
};

type ThemeProviderState = {
  theme: Theme;
  setTheme: (theme: Theme) => void;
};

const initialState: ThemeProviderState = {
  theme: "light",
  setTheme: () => null,
};

const ThemeProviderContext =
  React.createContext<ThemeProviderState>(initialState);

const isTheme = (value: string | null): value is Theme =>
  value === "light" || value === "dark";

const ThemeProvider = ({
  children,
  defaultTheme = "light",
  storageKey = "identitycore-theme",
  ...props
}: ThemeProviderProps) => {
  const [theme, setTheme] = React.useState<Theme>(defaultTheme);
  const [mounted, setMounted] = React.useState(false);

  React.useEffect(() => {
    setMounted(true);

    const storedTheme = window.localStorage.getItem(storageKey);
    const initialTheme = isTheme(storedTheme)
      ? storedTheme
      : window.matchMedia("(prefers-color-scheme: dark)").matches
        ? "dark"
        : defaultTheme;

    setTheme(initialTheme);
  }, [defaultTheme, storageKey]);

  React.useEffect(() => {
    if (!mounted) return;

    const root = window.document.documentElement;

    root.classList.remove("light", "dark");
    root.classList.add(theme);
  }, [mounted, theme]);

  const value = {
    theme: mounted ? theme : defaultTheme,
    setTheme: (theme: Theme) => {
      window.localStorage.setItem(storageKey, theme);
      setTheme(theme);
    },
  };

  return (
    <ThemeProviderContext.Provider {...props} value={value}>
      {children}
    </ThemeProviderContext.Provider>
  );
};

const useTheme = () => {
  const context = React.useContext(ThemeProviderContext);

  if (context === undefined)
    throw new Error("useTheme must be used within a ThemeProvider");

  return context;
};

export { ThemeProvider, useTheme };
