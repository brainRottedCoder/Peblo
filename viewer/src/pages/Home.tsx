import { useQuery } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { getCatalogue, img } from "../api";
import { Player } from "../components/Player";
import { Row } from "../components/PosterCard";

export function HomePage() {
  const q = useQuery({ queryKey: ["catalog"], queryFn: getCatalogue });
  const [reduce, setReduce] = useState(false);
  useEffect(() => {
    setReduce(window.matchMedia("(prefers-reduced-motion: reduce)").matches);
  }, []);

  if (q.isLoading) {
    return <div className="skel" style={{ height: "88vh" }} />;
  }
  if (q.isError) {
    return (
      <div className="empty">
        <h2>Peblo TV is taking a nap</h2>
        <p>{q.error.message}</p>
      </div>
    );
  }
  const data = q.data;
  const featured = data?.sections.find((s) => s.id === "featured")?.shows ?? [];
  const hero = featured[0] ?? data?.sections.flatMap((s) => s.shows)[0];
  if (!hero) {
    return (
      <div className="empty">
        <h2>Nothing on yet</h2>
        <p>An editor still needs to publish the catalogue.</p>
      </div>
    );
  }
  const poster = img(hero.artwork.banner) || img(hero.artwork.poster);
  return (
    <>
      <section className="hero">
        <div className="hero-media">
          {reduce || !hero.playback_url ? (
            <img src={poster} alt="" />
          ) : (
            <Player src={hero.playback_url} poster={poster} autoPlay muted loop />
          )}
        </div>
        <div className="hero-copy">
          <h1>{hero.title}</h1>
          <p>{hero.synopsis}</p>
          <div className="hero-actions">
            <Link to={`/watch/${hero.slug}`}>
              <button type="button" className="btn-play">
                ▶ Play
              </button>
            </Link>
            <Link to={`/show/${hero.slug}`}>
              <button type="button" className="btn-info">
                ℹ More info
              </button>
            </Link>
          </div>
        </div>
      </section>
      <div className="rows">
        {data?.sections.map((section) => (
          <Row key={section.id} title={section.title} shows={section.shows} />
        ))}
      </div>
    </>
  );
}
