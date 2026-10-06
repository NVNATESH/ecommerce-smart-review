/** Central API layer (spec section 50). All backend calls live here. */
import type {
  AnalysisResponse,
  AnalysisStatus,
  AnalysisSummary,
  ApiErrorBody,
  AskResponse,
  CompareProduct,
  CompareResponse,
  ModelInfo,
  ProductListItem,
  ReviewPage,
} from "./types";

export type { ProductListItem, CompareProduct, CompareResponse } from "./types";

export type { AskResponse };

export interface ProductDetail {
  success: boolean;
  id: string;
  name: string;
  created_at: string;
  updated_at: string;
  review_count: number;
  analysis_id: string | null;
  summary: AnalysisSummary | null;
}

export const API_URL =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

const BASE = `${API_URL}/api`;

export class ApiRequestError extends Error {
  code: string;
  status: number;
  details?: Record<string, unknown>;

  constructor(code: string, message: string, status: number, details?: Record<string, unknown>) {
    super(message);
    this.code = code;
    this.status = status;
    this.details = details;
  }
}

async function request<T>(path: string, init?: RequestInit, timeoutMs = 120_000): Promise<T> {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);
  try {
    const res = await fetch(`${BASE}${path}`, {
      ...init,
      signal: init?.signal ?? controller.signal,
      headers: { ...(init?.body ? { "Content-Type": "application/json" } : {}), ...init?.headers },
    });
    if (!res.ok) {
      let code = `HTTP_${res.status}`;
      let message = res.statusText;
      let details: Record<string, unknown> | undefined;
      try {
        const body = (await res.json()) as ApiErrorBody;
        if (body?.error) {
          code = body.error.code;
          message = body.error.message;
          details = body.error.details;
        }
      } catch {
        /* non-JSON error body */
      }
      throw new ApiRequestError(code, message, res.status, details);
    }
    return (await res.json()) as T;
  } finally {
    clearTimeout(timer);
  }
}

export function analyzeText(text: string, productName?: string, signal?: AbortSignal): Promise<AnalysisResponse> {
  return request<AnalysisResponse>("/analyze/text", {
    method: "POST",
    body: JSON.stringify({ text, ...(productName ? { product_name: productName } : {}) }),
    signal,
  });
}

export function uploadCSV(
  file: File,
  onProgress?: (pct: number) => void,
  productName?: string,
): Promise<AnalysisStatus> {
  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest();
    xhr.open("POST", `${BASE}/analyze/csv`);
    xhr.upload.onprogress = (e) => {
      if (e.lengthComputable && onProgress) onProgress(Math.round((e.loaded / e.total) * 100));
    };
    xhr.onload = () => {
      if (xhr.status >= 200 && xhr.status < 300) {
        resolve(JSON.parse(xhr.responseText) as AnalysisStatus);
      } else {
        try {
          const body = JSON.parse(xhr.responseText) as ApiErrorBody;
          reject(new ApiRequestError(body.error.code, body.error.message, xhr.status, body.error.details));
        } catch {
          reject(new ApiRequestError(`HTTP_${xhr.status}`, xhr.statusText, xhr.status));
        }
      }
    };
    xhr.onerror = () => reject(new ApiRequestError("NETWORK_ERROR", "Could not reach the server.", 0));
    const form = new FormData();
    form.append("file", file);
    if (productName) form.append("product_name", productName);
    xhr.send(form);
  });
}

export function getAnalysisStatus(analysisId: string, signal?: AbortSignal): Promise<AnalysisStatus> {
  return request<AnalysisStatus>(`/analysis/${analysisId}/status`, { signal });
}

export function getAnalysis(analysisId: string, signal?: AbortSignal): Promise<AnalysisSummary> {
  return request<AnalysisSummary>(`/analysis/${analysisId}`, { signal });
}

export function getReviews(
  analysisId: string,
  params: {
    page?: number;
    page_size?: number;
    status?: string;
    sentiment?: string;
    suspicious?: boolean;
    search?: string;
    sort?: string;
    order?: string;
  } = {},
  signal?: AbortSignal,
): Promise<ReviewPage> {
  const q = new URLSearchParams();
  Object.entries(params).forEach(([k, v]) => {
    if (v !== undefined && v !== null && v !== "") q.set(k, String(v));
  });
  return request<ReviewPage>(`/reviews/${analysisId}?${q.toString()}`, { signal });
}

export function getModels(signal?: AbortSignal): Promise<{ models: ModelInfo[] }> {
  return request<{ models: ModelInfo[] }>("/models", { signal });
}

export function askReview(analysisId: string, q: string, signal?: AbortSignal): Promise<AskResponse> {
  return request<AskResponse>(`/ask/${analysisId}?q=${encodeURIComponent(q)}`, { signal }, 30000);
}

export function listProducts(signal?: AbortSignal): Promise<{ success: boolean; products: ProductListItem[] }> {
  return request(`/products`, { signal });
}

export function getProduct(pid: string, signal?: AbortSignal): Promise<ProductDetail> {
  return request<ProductDetail>(`/products/${pid}`, { signal });
}

export function addProductReviews(
  pid: string,
  texts: string[],
  signal?: AbortSignal,
): Promise<{ success: boolean; analysis_id: string; product_analysis_id: string; review_count: number; summary: AnalysisSummary }> {
  return request(`/products/${pid}/reviews`, {
    method: "POST",
    body: JSON.stringify({ texts }),
    signal,
  });
}

export function deleteProduct(pid: string, signal?: AbortSignal): Promise<{ success: boolean }> {
  return request(`/products/${pid}`, { method: "DELETE", signal });
}

export function compareProducts(ids: string[], signal?: AbortSignal): Promise<CompareResponse> {
  return request<CompareResponse>(`/compare?ids=${ids.map(encodeURIComponent).join(",")}`, { signal }, 60000);
}

export function exportUrl(analysisId: string, format: string): string {
  return `${BASE}/export/${analysisId}?format=${format}`;
}
