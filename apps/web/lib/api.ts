export function apiBase(): string {
  const configured = process.env.NEXT_PUBLIC_API_URL;
  if (configured && configured.trim()) {
    return configured.trim().replace(/\/$/, "");
  }
  return "http://localhost:8000";
}

export function isHttpUrl(url: string): boolean {
  return url.startsWith("https://") || url.startsWith("http://");
}
