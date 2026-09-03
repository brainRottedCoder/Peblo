import type { ReactNode } from "react";
import { ApiError } from "../api";

export function Loading({ label = "Loading…" }: { label?: string }) {
  return <div className="empty">{label}</div>;
}

export function Empty({ title, body }: { title: string; body: string }) {
  return (
    <div className="empty">
      <strong>{title}</strong>
      <p>{body}</p>
    </div>
  );
}

export function ErrorBanner({ error }: { error: unknown }) {
  if (error instanceof ApiError && error.status === 403) {
    return (
      <div className="banner err" role="alert">
        You don’t have permission for this. Sign in as an admin if you need to publish.
      </div>
    );
  }
  const message = error instanceof Error ? error.message : "Something went wrong. Try again.";
  return (
    <div className="banner err" role="alert">
      {message}
    </div>
  );
}

export function Panel({ children }: { children: ReactNode }) {
  return <div className="card">{children}</div>;
}
