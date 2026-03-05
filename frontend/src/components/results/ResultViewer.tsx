import type { ComponentType, ReactElement } from "react";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Document, DocumentStructuredTable } from "@/types/document";

import { FieldsRenderer } from "./FieldsRenderer";
import { TableRenderer } from "./TableRenderer";

interface TextRendererProps {
  text: string;
}

interface TablesRendererProps {
  tablas: DocumentStructuredTable[];
}

interface FieldsRendererProps {
  campos: Record<string, string>;
}

interface ResultViewerRenderers {
  text?: ComponentType<TextRendererProps>;
  tables?: ComponentType<TablesRendererProps>;
  fields?: ComponentType<FieldsRendererProps>;
}

interface ResultViewerProps {
  document: Document;
  renderers?: ResultViewerRenderers;
}

function DefaultTextRenderer({ text }: TextRendererProps): ReactElement {
  return <pre className="whitespace-pre-wrap text-sm leading-6">{text || "Sin texto extraido"}</pre>;
}

export function ResultViewer({ document, renderers }: ResultViewerProps): ReactElement {
  const TextRenderer = renderers?.text ?? DefaultTextRenderer;
  const TablesRenderer = renderers?.tables ?? TableRenderer;
  const CustomFieldsRenderer = renderers?.fields ?? FieldsRenderer;

  const structured = document.structured_json ?? {
    texto: document.raw_text ?? "",
    tablas: [],
    campos: {},
  };

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Texto Completo</CardTitle>
        </CardHeader>
        <CardContent>
          <TextRenderer text={structured.texto || document.raw_text || ""} />
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Tablas</CardTitle>
        </CardHeader>
        <CardContent>
          <TablesRenderer tablas={structured.tablas} />
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Campos</CardTitle>
        </CardHeader>
        <CardContent>
          <CustomFieldsRenderer campos={structured.campos} />
        </CardContent>
      </Card>
    </div>
  );
}
