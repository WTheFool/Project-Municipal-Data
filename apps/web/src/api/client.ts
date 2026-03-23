import axios from "axios";

export const API_BASE = import.meta.env.VITE_API_BASE ?? "http://localhost:8000";

const client = axios.create({
  baseURL: API_BASE,
});

export default client;

export async function apiGet<T>(path: string): Promise<T> {
  const r = await client.get<T>(path);
  return r.data;
}

export async function apiPostJson<T>(path: string, body: any): Promise<T> {
  const r = await client.post<T>(path, body);
  return r.data;
}

export async function apiPostQuery<T>(path: string, params: Record<string, string>): Promise<T> {
  const r = await client.post<T>(path, undefined, { params });
  return r.data;
}

export async function apiUploadFile<T>(path: string, file: File): Promise<T> {
  const fd = new FormData();
  fd.append("file", file);
  const r = await client.post<T>(path, fd);
  return r.data;
}
