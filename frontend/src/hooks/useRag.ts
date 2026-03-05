import { useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";

import { indexDocument } from "@/services/api";

export function useIndexDocument() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (documentId: string) => indexDocument(documentId),
    onSuccess: (data) => {
      toast.success(`Documento indexado: ${data.chunks_indexed} fragmentos listos para chat`);
      queryClient.invalidateQueries({ queryKey: ["documents"] });
    },
    onError: () => {
      toast.error("Error al indexar el documento");
    },
  });
}
