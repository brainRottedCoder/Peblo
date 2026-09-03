import { useQuery } from "@tanstack/react-query";
import { useRef, useState } from "react";
import { Link } from "react-router-dom";
import { api, mediaUrl } from "../api";
import { Empty, ErrorBanner, Loading } from "../components/States";
import { useDebounced } from "../hooks";
import { useGsapEnter } from "../motion";
import { LANGUAGES, SECTIONS, type Show, type ShowList } from "../types";

function posterOf(show: Show) {
  return show.artwork.find((a) => a.kind === "poster") ?? show.artwork[0];
}

export function ShowsPage() {
  const root = useRef<HTMLDivElement>(null);
  const [q, setQ] = useState("");
  const debouncedQ = useDebounced(q, 300);
  const [section, setSection] = useState("");
  const [status, setStatus] = useState("");
  const [language, setLanguage] = useState("");
  const [page, setPage] = useState(1);

  const query = useQuery({
    queryKey: ["shows", debouncedQ, section, status, language, page],
    queryFn: () => {
      const params = new URLSearchParams({ page: String(page), page_size: "12" });
      if (debouncedQ) params.set("q", debouncedQ);
      if (section) params.set("section", section);
      if (status) params.set("status", status);
      if (language) params.set("language", language);
      return api<ShowList>(`/admin/shows?${params}`);
    },
  });

  useGsapEnter(root, ".page-head [data-anim], .filters");
  useGsapEnter(root, ".show-card", [query.data?.page, query.data?.items.length]);

  return (
    <div className="page" ref={root}>
      <header className="page-head">
        <div>
          <p className="kicker" data-anim>
            Library
          </p>
          <h1 data-anim>Shows</h1>
          <p className="lede" data-anim>
            Search, filter, then open a title to hang artwork or change episode status.
          </p>
        </div>
        <Link to="/shows/new" className="btn-link" data-anim>
          New show
        </Link>
      </header>
      <div className="filters" data-anim>
        <input
          placeholder="Search title or slug"
          value={q}
          onChange={(e) => {
            setQ(e.target.value);
            setPage(1);
          }}
          aria-label="Search title or slug"
        />
        <select
          value={section}
          onChange={(e) => {
            setSection(e.target.value);
            setPage(1);
          }}
          aria-label="Section"
        >
          <option value="">All sections</option>
          {SECTIONS.map((s) => (
            <option key={s.id} value={s.id}>
              {s.label}
            </option>
          ))}
        </select>
        <select
          value={status}
          onChange={(e) => {
            setStatus(e.target.value);
            setPage(1);
          }}
          aria-label="Status"
        >
          <option value="">All statuses</option>
          <option value="published">Published</option>
          <option value="draft">Draft</option>
        </select>
        <select
          value={language}
          onChange={(e) => {
            setLanguage(e.target.value);
            setPage(1);
          }}
          aria-label="Language"
        >
          <option value="">All languages</option>
          {LANGUAGES.map((l) => (
            <option key={l.id} value={l.id}>
              {l.label}
            </option>
          ))}
        </select>
      </div>
      {query.isLoading && <Loading label="Loading shows…" />}
      {query.isError && <ErrorBanner error={query.error} />}
      {query.data && query.data.items.length === 0 && (
        <Empty title="No shows match" body="Clear a filter or try a shorter search." />
      )}
      {query.data && query.data.items.length > 0 && (
        <>
          <div className="show-grid">
            {query.data.items.map((show) => {
              const art = posterOf(show);
              return (
                <Link key={show.id} className="show-card" to={`/shows/${show.id}`} data-anim>
                  <div className="show-poster">
                    {art ? (
                      <img src={mediaUrl(art.url)} alt="" />
                    ) : (
                      <div className="show-poster-empty">No poster</div>
                    )}
                  </div>
                  <div className="show-meta">
                    <h2>{show.title}</h2>
                    <p className="mono">{show.slug}</p>
                    <div className="show-row">
                      <span>{show.section ?? "No section"}</span>
                      <span className={`badge ${show.status}`}>{show.status}</span>
                    </div>
                    <p className="hint">{show.episode_count} episodes</p>
                  </div>
                </Link>
              );
            })}
          </div>
          <div className="pager" data-anim>
            <button className="ghost" disabled={page <= 1} onClick={() => setPage((p) => p - 1)}>
              Previous
            </button>
            <span>
              Page {query.data.page} · {query.data.total} shows
            </span>
            <button
              className="ghost"
              disabled={page * query.data.page_size >= query.data.total}
              onClick={() => setPage((p) => p + 1)}
            >
              Next
            </button>
          </div>
        </>
      )}
    </div>
  );
}
