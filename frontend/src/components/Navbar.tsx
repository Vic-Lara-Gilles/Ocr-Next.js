"use client";

import { LogOut, Moon, Sun } from "lucide-react";
import { useTheme } from "next-themes";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import type { ReactElement } from "react";

import { Button } from "@/components/ui/button";
import { useAuth } from "@/hooks/useAuth";

export function Navbar(): ReactElement {
  const pathname = usePathname();
  const router = useRouter();
  const { user, logout } = useAuth();
  const { theme, setTheme } = useTheme();

  const linkClass = (href: string) =>
    `text-sm font-medium transition-colors ${pathname === href
      ? "text-foreground"
      : "text-muted-foreground hover:text-foreground"
    }`;

  function handleLogout(): void {
    logout();
    router.push("/login");
  }

  return (
    <header className="sticky top-0 z-50 border-b bg-background/80 backdrop-blur-sm">
      <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-3">
        <Link href="/" className="text-base font-semibold tracking-tight">
          OCR Platform
        </Link>
        <nav className="flex items-center gap-4">
          {user ? (
            <>
              <Link href="/" className={linkClass("/")}>
                Subir PDF
              </Link>
              <Link href="/dashboard" className={linkClass("/dashboard")}>
                Dashboard
              </Link>
              <span className="text-sm text-muted-foreground">{user.name}</span>
              <Button variant="ghost" size="icon" onClick={handleLogout} title="Cerrar sesión">
                <LogOut className="h-4 w-4" />
              </Button>
            </>
          ) : (
            <>
              <Link href="/login" className={linkClass("/login")}>
                Iniciar Sesión
              </Link>
              <Link href="/register" className={linkClass("/register")}>
                Registrarse
              </Link>
            </>
          )}
          <Button
            variant="ghost"
            size="icon"
            onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
            title="Cambiar tema"
          >
            <Sun className="h-4 w-4 rotate-0 scale-100 transition-all dark:-rotate-90 dark:scale-0" />
            <Moon className="absolute h-4 w-4 rotate-90 scale-0 transition-all dark:rotate-0 dark:scale-100" />
          </Button>
        </nav>
      </div>
    </header>
  );
}
