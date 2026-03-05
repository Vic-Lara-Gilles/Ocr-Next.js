"use client";

import { useMutation } from "@tanstack/react-query";

import { uploadDocument } from "@/services/api";
import { Document } from "@/types/document";

interface UseUploadResult {
  uploadFile: (file: File) => Promise<Document>;
  isLoading: boolean;
  error: Error | null;
  result: Document | null;
}

export function useUpload(): UseUploadResult {
  const mutation = useMutation({
    mutationFn: uploadDocument,
  });

  return {
    uploadFile: mutation.mutateAsync,
    isLoading: mutation.isPending,
    error: (mutation.error as Error | null) ?? null,
    result: mutation.data ?? null,
  };
}
