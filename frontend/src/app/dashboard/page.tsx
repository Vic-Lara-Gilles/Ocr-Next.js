"use client";

import type { ReactElement } from "react";

import { DocumentList } from "@/components/documents/DocumentList";
import { ProtectedRoute } from "@/components/ProtectedRoute";

export default function DashboardPage(): ReactElement {
  return (
    <ProtectedRoute>
      <main className="min-h-screen bg-background p-6 md:p-10">
        <div className="mx-auto max-w-6xl space-y-6">
          <div className="flex items-center justify-between">
            <h1 className="text-3xl font-semibold">Dashboard</h1>
          </div>
          <DocumentList />
        </div>
      </main>
    </ProtectedRoute>
  );
}
