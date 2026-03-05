import type { ReactElement } from "react";

import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { DocumentStructuredTable } from "@/types/document";

interface TableRendererProps {
  tablas: DocumentStructuredTable[];
}

export function TableRenderer({ tablas }: TableRendererProps): ReactElement {
  if (tablas.length === 0) {
    return <p className="text-sm text-muted-foreground">No se detectaron tablas.</p>;
  }

  return (
    <div className="space-y-6">
      {tablas.map((table, index) => (
        <div key={`table-${index}`} className="rounded-lg border bg-white p-2 shadow-sm">
          <Table>
            <TableHeader>
              <TableRow>
                {table.headers.map((header, headerIndex) => (
                  <TableHead key={`header-${index}-${headerIndex}`}>{header}</TableHead>
                ))}
              </TableRow>
            </TableHeader>
            <TableBody>
              {table.rows.map((row, rowIndex) => (
                <TableRow key={`row-${index}-${rowIndex}`}>
                  {row.map((cell, cellIndex) => (
                    <TableCell key={`cell-${index}-${rowIndex}-${cellIndex}`}>{cell}</TableCell>
                  ))}
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      ))}
    </div>
  );
}
