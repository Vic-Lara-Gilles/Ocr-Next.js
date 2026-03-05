"use client";

import { FileText, Loader2 } from "lucide-react";
import Link from "next/link";
import { useParams } from "next/navigation";
import type { ReactElement } from "react";
import { useEffect, useMemo, useRef, useState } from "react";

import { ResultViewer } from "@/components/results/ResultViewer";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
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

const STEPS = [
  "Leyendo el documento...",
  "Analizando páginas con IA...",
  "Extrayendo texto y tablas...",
  "Estructurando los datos...",
];

function ProcessingCard({ filename, pages }: { filename?: string; pages?: number }): ReactElement {
  const [progress, setProgress] = useState(0);
  const [stepIndex, setStepIndex] = useState(0);
  const [elapsed, setElapsed] = useState(0);
  const startRef = useRef(Date.now());

  // Estimated total time: 5s base + 4s per page, capped at 120s for display
  const estimated = Math.min(5000 + (pages ?? 1) * 4000, 120000);

  useEffect(() => {
    const interval = setInterval(() => {
      const spent = Date.now() - startRef.current;
      setElapsed(Math.floor(spent / 1000));
      // Ease toward 90%, never reaching 100 until done
      const raw = Math.min((spent / estimated) * 90, 90);
      setProgress(Math.round(raw));
      setStepIndex(Math.min(Math.floor((spent / estimated) * STEPS.length), STEPS.length - 1));
    }, 300);
    return () => clearInterval(interval);
  }, [estimated]);

  return (
    <main className="flex min-h-screen items-center justify-center bg-slate-50 p-6">
      <Card className="w-full max-w-lg border-0 bg-white shadow-2xl">
        <CardHeader className="pb-2 text-center">
          <div className="mx-auto mb-3 flex h-14 w-14 items-center justify-center rounded-full bg-slate-100">
            <FileText className="h-7 w-7 text-slate-600" />
          </div>
          <CardTitle className="text-xl">Procesando documento</CardTitle>
          {filename && (
            <p className="truncate text-sm text-muted-foreground">{filename}</p>
          )}
        </CardHeader>
        <CardContent className="space-y-6 pt-2">
          <div className="space-y-2">
            <div className="flex justify-between text-xs text-muted-foreground">
              <span>{progress}%</span>
              {pages && <span>{pages} {pages === 1 ? "página" : "páginas"}</span>}
            </div>
            <Progress value={progress} className="h-2.5" />
          </div>

          <div className="flex items-center gap-2 rounded-lg bg-slate-50 px-4 py-3">
            <Loader2 className="h-4 w-4 shrink-0 animate-spin text-slate-500" />
            <span className="text-sm text-slate-600">{STEPS[stepIndex]}</span>
          </div>

          <p className="text-center text-xs text-muted-foreground">
            {elapsed}s transcurridos · Esta pantalla se actualiza automáticamente
          </p>
        </CardContent>
      </Card>
    </main>
  );
}

export default function ResultPage(): ReactElement {
  const params = useParams<{ id: string }>();
  const documentId = params.id;
  const { document, isLoading, isError } = useDocumentStatus(documentId);

  const canRenderResult = useMemo(() => {
    return document?.status === "completed" || document?.status === "failed";
  }, [document]);

  if (isLoading || (document && (document.status === "processing" || document.status === "pending"))) {
    return <ProcessingCard filename={document?.filename} pages={document?.pages_count} />;
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
