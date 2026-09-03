import { Link } from "react-router-dom";
import { img } from "../api";
import type { CatalogueShow } from "../types";
import { SlowImage } from "./SlowImage";

export function PosterCard({ show }: { show: CatalogueShow }) {
  return (
    <Link className="poster" to={`/show/${show.slug}`}>
      <SlowImage src={img(show.artwork.poster) || img(show.artwork.banner)} alt={show.title} ratio="2 / 3" />
      <span className="poster-meta">{show.title}</span>
    </Link>
  );
}

export function Row({ title, shows }: { title: string; shows: CatalogueShow[] }) {
  if (shows.length === 0) return null;
  return (
    <section className="row">
      <h2>{title}</h2>
      <div className="scroller">
        {shows.map((show) => (
          <PosterCard key={show.id} show={show} />
        ))}
      </div>
    </section>
  );
}
