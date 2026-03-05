"use client";

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useState } from "react";
import { Toaster } from "sonner";
import "./globals.css";

import { Navbar } from "@/components/Navbar";

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  const [queryClient] = useState<QueryClient>(() => new QueryClient());

  return (
    <html lang="en">
      <body className="antialiased">
        <QueryClientProvider client={queryClient}>
          <Navbar />
          {children}
          <Toaster richColors position="top-right" />
        </QueryClientProvider>
      </body>
    </html>
  );
}
