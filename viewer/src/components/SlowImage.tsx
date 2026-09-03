import { useState } from "react";

export function SlowImage({ src, alt, ratio }: { src?: string; alt: string; ratio: string }) {
  const [ready, setReady] = useState(false);
  return (
    <div style={{ position: "relative", aspectRatio: ratio, background: "#1c1814" }}>
      {!ready && <div className="skel" style={{ position: "absolute", inset: 0 }} aria-hidden />}
      {src ? (
        <img
          src={src}
          alt={alt}
          loading="lazy"
          onLoad={() => setReady(true)}
          style={{ width: "100%", height: "100%", objectFit: "cover", opacity: ready ? 1 : 0, transition: "opacity 200ms ease-out" }}
        />
      ) : (
        <div style={{ position: "absolute", inset: 0, display: "grid", placeItems: "center", color: "#c9bba8", fontSize: 12 }}>
          Picture coming soon
        </div>
      )}
    </div>
  );
}
