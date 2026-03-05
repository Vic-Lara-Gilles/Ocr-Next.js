import Link from "next/link";
import type { ReactElement } from "react";

import { DocumentList } from "@/components/documents/DocumentList";

export default function DashboardPage(): ReactElement {
  return (
    <main className="min-h-screen bg-slate-50 p-6 md:p-10">
      <div className="mx-auto max-w-6xl space-y-6">
        <div className="flex items-center justify-between">
          <h1 className="text-3xl font-semibold">Dashboard</h1>
          <Link href="/" className="text-sm font-medium text-blue-700 hover:underline">
            Volver a subir documento
          </Link>
        </div>
        <DocumentList />
      </div>
    </main>
  );
}
