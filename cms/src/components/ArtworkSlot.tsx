import { DragEvent, useRef, useState } from "react";
import { api, mediaUrl, ApiError } from "../api";
import type { Artwork } from "../types";
import { SPECS } from "../types";

type Props = {
  kind: "poster" | "banner" | "thumbnail";
  current?: Artwork;
  endpoint: string;
  onUploaded: (art: Artwork) => void;
  compact?: boolean;
};

export function ArtworkSlot({ kind, current, endpoint, onUploaded, compact }: Props) {
  const spec = SPECS[kind];
  const [preview, setPreview] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [over, setOver] = useState(false);
  const fileInputRef = useRef<HTMLInputElement | null>(null);

  async function onFile(file: File) {
    setError(null);
    setPreview(URL.createObjectURL(file));
    const body = new FormData();
    body.append("kind", kind);
    body.append("file", file);
    setBusy(true);
    try {
      const art = await api<Artwork>(endpoint, { method: "POST", body });
      onUploaded(art);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Upload failed. Try another file.");
    } finally {
      setBusy(false);
    }
  }

  function drop(e: DragEvent) {
    e.preventDefault();
    setOver(false);
    const file = e.dataTransfer.files?.[0];
    if (file) void onFile(file);
  }

  const src = preview || (current ? mediaUrl(current.url) : null);

  return (
    <div
      className={`slot ${kind} ${compact ? "compact" : ""} ${over ? "over" : ""}`}
      onDragOver={(e) => {
        e.preventDefault();
        setOver(true);
      }}
      onDragLeave={() => setOver(false)}
      onDrop={drop}
    >
      <strong>{spec.label}</strong>
      {compact ? null : (
        <div className="hint">
          {spec.aspect}. Target {spec.size}. 200 KB max.
        </div>
      )}
      {src ? <img src={src} alt={`${spec.label} preview`} /> : <div className="empty-slot">Drop a JPEG or PNG</div>}
      <input
        ref={fileInputRef}
        type="file"
        accept="image/jpeg,image/png"
        aria-label={`Upload ${spec.label}`}
        disabled={busy}
        onChange={(e) => {
          const input = e.currentTarget;
          const file = input.files?.[0];
          if (file) void onFile(file);
          // Browsers won't fire `onChange` if the same file is picked twice; clear the value.
          input.value = "";
        }}
      />
      {busy && <div className="hint">Checking size and saving…</div>}
      {error && <div className="err">{error}</div>}
    </div>
  );
}
