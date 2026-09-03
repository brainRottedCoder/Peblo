import { useQuery } from "@tanstack/react-query";
import { Link, useParams, useSearchParams } from "react-router-dom";
import { getCatalogue, img } from "../api";

export function WatchPage() {
  const { slug } = useParams();
  const [params] = useSearchParams();
  const q = useQuery({ queryKey: ["catalog"], queryFn: getCatalogue });
  const show = q.data?.sections.flatMap((s) => s.shows).find((s) => s.slug === slug);
  const epId = params.get("ep");
  const lang = params.get("lang");
  const episode =
    show?.seasons.flatMap((s) => s.episodes).find((e) => e.content_group === epId) ||
    show?.trailers.find((e) => e.content_group === epId);
  const src =
    (lang && episode?.playback_by_language?.[lang]) || episode?.playback_url || show?.playback_url;
  const episodeTitle = (lang && episode?.titles_by_language?.[lang]) || episode?.title;
  const poster = img(episode?.artwork.banner) || img(show?.artwork.banner) || img(show?.artwork.poster);

  if (q.isLoading) return <div className="skel" style={{ height: "100vh" }} />;
  if (!show || !src) {
    return (
      <div className="empty">
        <h2>This title isn’t playing</h2>
        <p>
          <Link to="/">Home</Link>
        </p>
      </div>
    );
  }

  return (
    <div className="player-page">
      <div className="player-bar">
        <Link to={`/show/${show.slug}`}>← Back</Link>
        <strong>
          {show.title}
          {episodeTitle ? ` · ${episodeTitle}` : ""}
        </strong>
      </div>
      <video src={src} poster={poster} autoPlay controls playsInline />
    </div>
  );
}
