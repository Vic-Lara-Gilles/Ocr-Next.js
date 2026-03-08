"use client";

import { ProtectedRoute } from "@/components/ProtectedRoute";
import { UploadZone } from "@/components/upload/UploadZone";

export default function Home() {
  return (
    <ProtectedRoute>
      <div className="min-h-screen bg-background p-6 md:p-10">
        <main className="mx-auto flex min-h-[90vh] max-w-6xl flex-col items-center justify-center gap-6">
          <h1 className="text-center text-4xl font-semibold tracking-tight md:text-5xl">OCR Platform</h1>
          <p className="max-w-2xl text-center text-sm text-muted-foreground md:text-base">
            Extrae texto, tablas y campos estructurados desde documentos PDF con un pipeline OCR escalable.
          </p>
          <UploadZone />
        </main>
      </div>
    </ProtectedRoute>
  );
}
