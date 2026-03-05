import axios, { AxiosInstance } from "axios";

import { Document } from "@/types/document";

const apiClient: AxiosInstance = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL,
  timeout: 60000,
});

export async function uploadDocument(file: File): Promise<Document> {
  const formData = new FormData();
  formData.append("file", file);
  const response = await apiClient.post<Document>("/api/upload", formData, {
    headers: {
      "Content-Type": "multipart/form-data",
    },
  });
  return response.data;
}

export async function getDocumentResult(id: string): Promise<Document> {
  const response = await apiClient.get<Document>(`/api/results/${id}`);
  return response.data;
}

export async function listDocuments(): Promise<Document[]> {
  const response = await apiClient.get<Document[]>("/api/documents");
  return response.data;
}
