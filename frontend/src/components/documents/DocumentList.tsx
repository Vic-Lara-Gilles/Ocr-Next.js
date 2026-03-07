"use client";

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

  return (
    <div className="rounded-xl border bg-white p-4 shadow-sm">
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
                <Link className="text-sm font-medium text-blue-700 hover:underline" href={`/results/${document.id}`}>
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
                  <Link className="text-sm font-medium text-blue-700 hover:underline" href={`/chat/${document.id}`}>
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
