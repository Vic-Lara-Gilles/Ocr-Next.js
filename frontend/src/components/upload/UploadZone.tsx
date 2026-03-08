"use client";

import { UploadCloud } from "lucide-react";
import { useRouter } from "next/navigation";
import type { ReactElement } from "react";
import { useEffect, useMemo, useState } from "react";
import { useDropzone } from "react-dropzone";
import { toast } from "sonner";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { useUpload } from "@/hooks/useUpload";

export function UploadZone(): ReactElement {
  const router = useRouter();
  const { uploadFile, isLoading } = useUpload();
  const [progress, setProgress] = useState<number>(0);

  useEffect(() => {
    if (!isLoading) {
      setProgress(0);
      return;
    }

    const timer = setInterval(() => {
      setProgress((value) => (value >= 90 ? 90 : value + 10));
    }, 250);

    return () => clearInterval(timer);
  }, [isLoading]);

  const onDrop = async (acceptedFiles: File[]): Promise<void> => {
    const file = acceptedFiles[0];
    if (!file) {
      return;
    }

    try {
      const result = await uploadFile(file);
      setProgress(100);
      toast.success("Documento recibido correctamente");
      router.push(`/results/${result.id}`);
    } catch (error) {
      setProgress(0);
      toast.error(error instanceof Error ? error.message : "No se pudo subir el documento");
    }
  };

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      "application/pdf": [".pdf"],
    },
    multiple: false,
    maxFiles: 1,
  });

  const containerClassName = useMemo(() => {
    return isDragActive
      ? "border-primary bg-primary/10"
      : "border-border bg-background hover:border-primary/70";
  }, [isDragActive]);

  return (
    <Card className="w-full max-w-2xl border-0 bg-card/90 shadow-2xl backdrop-blur-sm">
      <CardHeader>
        <CardTitle className="text-2xl">Sube tu PDF</CardTitle>
        <CardDescription>
          Arrastra un archivo PDF para extraer texto, tablas y campos estructurados.
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div
          {...getRootProps()}
          className={`cursor-pointer rounded-xl border-2 border-dashed p-10 text-center transition-all ${containerClassName}`}
        >
          <input {...getInputProps()} />
          <UploadCloud className="mx-auto mb-4 h-10 w-10" />
          <p className="text-sm font-medium">
            {isDragActive ? "Suelta el PDF aquí" : "Arrastra y suelta tu PDF o haz clic para seleccionarlo"}
          </p>
          <p className="mt-2 text-xs text-muted-foreground">Solo archivos .pdf</p>
        </div>
        <div className="mt-4">
          <Progress value={progress} />
        </div>
      </CardContent>
    </Card>
  );
}
