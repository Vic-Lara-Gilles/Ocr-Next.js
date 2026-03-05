export type DocumentStatus = "pending" | "processing" | "completed" | "failed";

export interface DocumentStructuredTable {
  headers: string[];
  rows: string[][];
}

export interface DocumentStructuredJson {
  texto: string;
  tablas: DocumentStructuredTable[];
  campos: Record<string, string>;
}

export interface Document {
  id: string;
  filename: string;
  status: DocumentStatus;
  pages_count: number;
  raw_text: string | null;
  structured_json: DocumentStructuredJson | null;
  created_at: string;
  updated_at: string;
}
