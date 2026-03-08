"use client";

import { FileText, Upload } from "lucide-react";
import Link from "next/link";
import type { ReactElement } from "react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { useDocuments } from "@/hooks/useDocuments";
import { useIndexDocument } from "@/hooks/useRag";
import { DocumentStatus } from "@/types/document";

function badgeVariant(status: DocumentStatus): "default" | "secondary" | "destructive" | "outline" {
  if (status === "completed") {
    return "default";
  }
  if (status === "processing") {
    return "secondary";
  }
  if (status === "failed") {
    return "destructive";
  }
  return "outline";
}

export function DocumentList(): ReactElement {
  const { documents, isLoading, isError } = useDocuments();
  const { mutate: indexDoc, isPending, variables: indexingId } = useIndexDocument();

  if (isLoading) {
    return <p className="text-sm text-muted-foreground">Cargando documentos...</p>;
  }

  if (isError) {
    return <p className="text-sm text-destructive">No se pudieron cargar los documentos.</p>;
  }

  if (documents.length === 0) {
    return (
      <div className="rounded-xl border bg-card p-14 text-center shadow-sm">
        <FileText className="mx-auto mb-4 h-12 w-12 text-muted-foreground/50" />
        <h3 className="text-lg font-medium">No hay documentos todavía</h3>
        <p className="mt-1 text-sm text-muted-foreground">Sube tu primer PDF para comenzar a extraer texto y tablas.</p>
        <Link
          href="/"
          className="mt-5 inline-flex items-center gap-2 rounded-lg bg-primary px-4 py-2 text-sm font-medium text-primary-foreground transition-opacity hover:opacity-90"
        >
          <Upload className="h-4 w-4" />
          Subir PDF
        </Link>
      </div>
    );
  }

  return (
    <div className="rounded-xl border bg-card p-4 shadow-sm">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Archivo</TableHead>
            <TableHead>Paginas</TableHead>
            <TableHead>Estado</TableHead>
            <TableHead>Creado</TableHead>
            <TableHead>Resultado</TableHead>
            <TableHead>RAG</TableHead>
            <TableHead>Chat</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {documents.map((document) => (
            <TableRow key={document.id}>
              <TableCell>{document.filename}</TableCell>
              <TableCell>{document.pages_count}</TableCell>
              <TableCell>
                <Badge variant={badgeVariant(document.status)}>{document.status}</Badge>
              </TableCell>
              <TableCell>{new Date(document.created_at).toLocaleString()}</TableCell>
              <TableCell>
                <Link className="text-sm font-medium text-primary hover:underline" href={`/results/${document.id}`}>
                  Ver
                </Link>
              </TableCell>
              <TableCell>
                <Button
                  size="sm"
                  variant="outline"
                  disabled={document.status !== "completed" || (isPending && indexingId === document.id)}
                  onClick={() => indexDoc(document.id)}
                >
                  {isPending && indexingId === document.id ? "Indexando..." : "Indexar"}
                </Button>
              </TableCell>
              <TableCell>
                {document.status === "completed" ? (
                  <Link className="text-sm font-medium text-primary hover:underline" href={`/chat/${document.id}`}>
                    Chat
                  </Link>
                ) : (
                  <span className="text-sm text-muted-foreground">—</span>
                )}
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
}
