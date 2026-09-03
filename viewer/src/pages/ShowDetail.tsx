import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { getCatalogue, img } from "../api";
import { Player } from "../components/Player";
import type { CatalogueEpisode, CatalogueShow } from "../types";

function EpisodeRow({
  ep,
  onPlay,
}: {
  ep: CatalogueEpisode;
  onPlay: (lang: string) => void;
}) {
  const [lang, setLang] = useState(ep.languages[0]);
  const mins = ep.duration_seconds ? Math.round(ep.duration_seconds / 60) : null;
  const title = ep.titles_by_language?.[lang] || ep.title;
  return (
    <button type="button" className="ep" onClick={() => onPlay(lang)}>
      <span className="num">{ep.episode_number}</span>
      <span className="thumb">
        <img src={img(ep.artwork.thumbnail) || img(ep.artwork.poster)} alt="" />
        <span className="play-badge">▶</span>
      </span>
      <span>
        <strong>{title}</strong>
        <div style={{ color: "#b3b3b3", fontSize: 14 }}>{mins ? `${mins}m` : ""}</div>
      </span>
      <span className="langs" onClick={(e) => e.stopPropagation()}>
        {ep.languages.map((code) => (
          <span
            key={code}
            className={`lang ${lang === code ? "on" : ""}`}
            onClick={() => setLang(code)}
            onKeyDown={(e) => e.key === "Enter" && setLang(code)}
            role="button"
            tabIndex={0}
          >
            {code === "hi" ? "हिन्दी" : "EN"}
          </span>
        ))}
      </span>
    </button>
  );
}

export function ShowDetailPage() {
  const { slug } = useParams();
  const nav = useNavigate();
  const q = useQuery({ queryKey: ["catalog"], queryFn: getCatalogue });
  const show: CatalogueShow | undefined = q.data?.sections.flatMap((s) => s.shows).find((s) => s.slug === slug);

  if (q.isLoading) return <div className="skel" style={{ height: "72vh" }} />;
  if (!show) {
    return (
      <div className="empty">
        <h2>This title isn’t in the catalogue</h2>
        <p>
          <Link to="/">Back to Home</Link>
        </p>
      </div>
    );
  }
  const poster = img(show.artwork.banner) || img(show.artwork.poster);

  return (
    <>
      <div className="detail-billboard">
        {show.playback_url ? (
          <Player src={show.playback_url} poster={poster} autoPlay muted loop />
        ) : (
          <img src={poster} alt="" />
        )}
      </div>
      <div className="detail">
        <h1>{show.title}</h1>
        <div className="pills">
          {show.categories.map((c) => (
            <span key={c} style={{ color: "#b3b3b3" }}>
              {c}
            </span>
          ))}
        </div>
        <p className="lede">{show.synopsis}</p>
        <p>
          <Link to={`/watch/${show.slug}`}>
            <button type="button" className="btn-play">
              ▶ Play
            </button>
          </Link>
        </p>
        {show.trailers.length > 0 && (
          <section>
            <h2>Trailer</h2>
            <div className="episodes">
              {show.trailers.map((ep) => (
                <EpisodeRow
                  key={ep.content_group}
                  ep={ep}
                  onPlay={(lang) => nav(`/watch/${show.slug}?ep=${ep.content_group}&lang=${lang}`)}
                />
              ))}
            </div>
          </section>
        )}
        {show.seasons.map((season) => (
          <section key={season.number}>
            <h2>Season {season.number}</h2>
            <div className="episodes">
              {season.episodes.map((ep) => (
                <EpisodeRow
                  key={ep.content_group}
                  ep={ep}
                  onPlay={(lang) => nav(`/watch/${show.slug}?ep=${ep.content_group}&lang=${lang}`)}
                />
              ))}
            </div>
          </section>
        ))}
      </div>
    </>
  );
}
