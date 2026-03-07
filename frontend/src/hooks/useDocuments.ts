"use client";

import { useQuery } from "@tanstack/react-query";

import { listDocuments } from "@/services/api";
import { Document } from "@/types/document";

interface UseDocumentsResult {
  documents: Document[];
  isLoading: boolean;
  isError: boolean;
}

export function useDocuments(): UseDocumentsResult {
  const query = useQuery({
    queryKey: ["documents"],
    queryFn: listDocuments,
  });

  return {
    documents: query.data ?? [],
    isLoading: query.isLoading,
    isError: query.isError,
  };
}
