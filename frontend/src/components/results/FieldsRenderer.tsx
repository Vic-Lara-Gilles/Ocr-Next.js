import type { ReactElement } from "react";

interface FieldsRendererProps {
  campos: Record<string, string>;
}

export function FieldsRenderer({ campos }: FieldsRendererProps): ReactElement {
  const entries = Object.entries(campos);

  if (entries.length === 0) {
    return <p className="text-sm text-muted-foreground">No se detectaron campos estructurados.</p>;
  }

  return (
    <dl className="grid gap-3 md:grid-cols-2">
      {entries.map(([key, value]) => (
        <div key={key} className="rounded-lg border bg-white p-3">
          <dt className="text-xs uppercase tracking-wide text-muted-foreground">{key}</dt>
          <dd className="mt-1 text-sm font-medium">{value}</dd>
        </div>
      ))}
    </dl>
  );
}
