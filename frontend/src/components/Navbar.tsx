"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import type { ReactElement } from "react";

export function Navbar(): ReactElement {
  const pathname = usePathname();

  const linkClass = (href: string) =>
    `text-sm font-medium transition-colors ${pathname === href
      ? "text-foreground"
      : "text-muted-foreground hover:text-foreground"
    }`;

  return (
    <header className="sticky top-0 z-50 border-b bg-white/80 backdrop-blur-sm">
      <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-3">
        <Link href="/" className="text-base font-semibold tracking-tight">
          OCR Platform
        </Link>
        <nav className="flex items-center gap-6">
          <Link href="/" className={linkClass("/")}>
            Subir PDF
          </Link>
          <Link href="/dashboard" className={linkClass("/dashboard")}>
            Dashboard
          </Link>
        </nav>
      </div>
    </header>
  );
}
