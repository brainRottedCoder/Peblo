import { useRef, useState } from "react";
import { img } from "../api";

export function Player({
  src,
  poster,
  autoPlay = false,
  muted = false,
  loop = false,
  className,
}: {
  src?: string;
  poster?: string;
  autoPlay?: boolean;
  muted?: boolean;
  loop?: boolean;
  className?: string;
}) {
  const ref = useRef<HTMLVideoElement>(null);
  const [mute, setMute] = useState(muted);
  if (!src) {
    return poster ? <img className={className} src={poster} alt="" /> : <div className={`skel ${className ?? ""}`} />;
  }
  return (
    <div className="player-wrap">
      <video
        ref={ref}
        className={className}
        src={src}
        poster={poster}
        autoPlay={autoPlay}
        muted={mute}
        loop={loop}
        playsInline
        controls={!autoPlay}
        preload="metadata"
      />
      {autoPlay && (
        <button
          type="button"
          className="mute"
          aria-label={mute ? "Unmute" : "Mute"}
          onClick={() => {
            const next = !mute;
            setMute(next);
            if (ref.current) ref.current.muted = next;
          }}
        >
          {mute ? "🔇" : "🔊"}
        </button>
      )}
    </div>
  );
}

export { img };
