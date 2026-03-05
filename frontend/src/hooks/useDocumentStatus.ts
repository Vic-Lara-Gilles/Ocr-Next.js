"use client";

import { useQuery } from "@tanstack/react-query";

import { getDocumentResult } from "@/services/api";
import { Document } from "@/types/document";

interface UseDocumentStatusResult {
  document: Document | null;
  isLoading: boolean;
  isError: boolean;
}

export function useDocumentStatus(documentId: string | undefined): UseDocumentStatusResult {
  const query = useQuery({
    queryKey: ["document", documentId],
    queryFn: () => getDocumentResult(documentId as string),
    enabled: Boolean(documentId),
    refetchInterval: (data) => {
      const status = data?.state.data?.status;
      if (status === "completed" || status === "failed") {
        return false;
      }
      if (data?.state.error) {
        return false;
      }
      return 2000;
    },
    retry: false,
  });

  return {
    document: query.data ?? null,
    isLoading: query.isLoading,
    isError: query.isError,
  };
}
