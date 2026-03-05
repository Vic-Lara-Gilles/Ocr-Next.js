"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import type { ReactElement } from "react";
import { useMemo } from "react";

import { ResultViewer } from "@/components/results/ResultViewer";
import { Button } from "@/components/ui/button";
import { useDocumentStatus } from "@/hooks/useDocumentStatus";
import { Document } from "@/types/document";

function downloadFile(content: string, fileName: string, mimeType: string): void {
  const blob = new Blob([content], { type: mimeType });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = fileName;
  anchor.click();
  URL.revokeObjectURL(url);
}

export default function ResultPage(): ReactElement {
  const params = useParams<{ id: string }>();
  const documentId = params.id;
  const { document, isLoading, isError } = useDocumentStatus(documentId);

  const canRenderResult = useMemo(() => {
    return document?.status === "completed" || document?.status === "failed";
  }, [document]);

  if (isLoading || (document && document.status === "processing")) {
    return (
      <main className="min-h-screen bg-slate-50 p-6 md:p-10">
        <div className="mx-auto max-w-4xl space-y-4">
          <h1 className="text-2xl font-semibold">Procesando documento...</h1>
          <p className="text-sm text-muted-foreground">Estamos analizando el PDF. Esta pantalla se actualiza automaticamente.</p>
        </div>
      </main>
    );
  }

  if (isError || !document) {
    return (
      <main className="min-h-screen bg-slate-50 p-6 md:p-10">
        <div className="mx-auto max-w-4xl space-y-4">
          <h1 className="text-2xl font-semibold">No se encontro el documento</h1>
          <Link href="/dashboard" className="text-sm font-medium text-blue-700 hover:underline">
            Volver al dashboard
          </Link>
        </div>
      </main>
    );
  }

  return (
    <main className="min-h-screen bg-slate-50 p-6 md:p-10">
      <div className="mx-auto max-w-5xl space-y-6">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <h1 className="text-2xl font-semibold">Resultado: {document.filename}</h1>
            <p className="text-sm text-muted-foreground">Estado actual: {document.status}</p>
          </div>
          <div className="flex items-center gap-2">
            <Button
              type="button"
              variant="outline"
              onClick={() =>
                downloadFile(
                  JSON.stringify(document.structured_json, null, 2),
                  `ocr-${document.id}.json`,
                  "application/json"
                )
              }
              disabled={!document.structured_json}
            >
              Descargar JSON
            </Button>
            <Button
              type="button"
              onClick={() => downloadFile(document.raw_text ?? "", `ocr-${document.id}.txt`, "text/plain")}
              disabled={!document.raw_text}
            >
              Descargar Texto
            </Button>
          </div>
        </div>

        {canRenderResult ? <ResultViewer document={document as Document} /> : null}
      </div>
    </main>
  );
}
