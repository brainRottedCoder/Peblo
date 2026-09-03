import type { Catalogue, SearchResponse } from "./types";

const API = import.meta.env.VITE_API_URL || "http://localhost:8000";

export async function getCatalogue(): Promise<Catalogue> {
  const res = await fetch(`${API}/catalog`);
  if (!res.ok) throw new Error("The catalogue isn’t available right now.");
  return res.json();
}

export async function searchCatalogue(params: URLSearchParams): Promise<SearchResponse> {
  const res = await fetch(`${API}/catalog/search?${params}`);
  if (res.status === 404) return { q: null, category: null, language: null, section: null, results: [] };
  if (!res.ok) throw new Error("Search didn’t work. Try again in a moment.");
  return res.json();
}

export function img(url?: string): string | undefined {
  if (!url) return undefined;
  return url.startsWith("http") ? url : `${API}${url}`;
}
