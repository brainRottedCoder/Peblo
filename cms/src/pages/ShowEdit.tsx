import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { api } from "../api";
import { ArtworkSlot } from "../components/ArtworkSlot";
import { ErrorBanner, Loading } from "../components/States";
import {
  CATEGORIES,
  LANGUAGES,
  SECTIONS,
  type Artwork,
  type Episode,
  type Season,
  type ShowDetail,
} from "../types";

function kindOf(list: Artwork[], kind: Artwork["kind"]) {
  return list.find((a) => a.kind === kind);
}

export function ShowEditPage() {
  const { id } = useParams<{ id: string }>();
  const qc = useQueryClient();
  const showQ = useQuery({
    queryKey: ["show", id],
    queryFn: () => api<ShowDetail>(`/admin/shows/${id}`),
    enabled: Boolean(id),
  });
  const [formError, setFormError] = useState<unknown>(null);
  const [title, setTitle] = useState("");
  const [slug, setSlug] = useState("");
  const [synopsis, setSynopsis] = useState("");
  const [section, setSection] = useState("");
  const [status, setStatus] = useState<ShowDetail["status"]>("draft");
  const [categories, setCategories] = useState<string[]>([]);
  const [seasonNumber, setSeasonNumber] = useState(1);

  useEffect(() => {
    const show = showQ.data;
    if (!show) return;
    setTitle(show.title);
    setSlug(show.slug);
    setSynopsis(show.synopsis);
    setSection(show.section ?? "");
    setStatus(show.status);
    setCategories(show.categories);
  }, [showQ.data]);

  const saveShow = useMutation({
    mutationFn: (body: Partial<ShowDetail>) =>
      api<ShowDetail>(`/admin/shows/${id}`, { method: "PATCH", body: JSON.stringify(body) }),
    onSuccess: (data) => {
      qc.setQueryData(["show", id], data);
      setFormError(null);
    },
    onError: setFormError,
  });

  const addSeason = useMutation({
    mutationFn: () => api<Season>(`/admin/shows/${id}/seasons`, { method: "POST", body: JSON.stringify({ number: seasonNumber }) }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["show", id] }),
    onError: setFormError,
  });

  if (showQ.isLoading) return <Loading label="Opening show…" />;
  if (showQ.isError) {
    return (
      <div className="page">
        <ErrorBanner error={showQ.error} />
      </div>
    );
  }
  const show = showQ.data;
  if (!show) return null;

  return (
    <div className="page">
      <p>
        <Link to="/shows" className="back">
          ← All shows
        </Link>
      </p>
      <header className="page-head page-head-edit">
        <h1 className="sr-only">{title || show.title}</h1>
        <p className="kicker">{show.section ?? "Unsectioned"}</p>
        <span className={`badge ${show.status}`}>{show.status}</span>
      </header>
      {formError ? <ErrorBanner error={formError} /> : null}

      <form
        className="card"
        onSubmit={(e) => {
          e.preventDefault();
          saveShow.mutate({
            title,
            slug,
            synopsis,
            section: section || null,
            status,
            categories,
          });
        }}
      >
        <h2>Show details</h2>
        <label className="show-title-field">
          <span>Show title</span>
          <input
            className="show-title-input"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            required
          />
        </label>
        <div className="grid2">
          <label>
            <span>Section</span>
            <select value={section} onChange={(e) => setSection(e.target.value)}>
              <option value="">— none —</option>
              {SECTIONS.map((s) => (
                <option key={s.id} value={s.id}>
                  {s.label}
                </option>
              ))}
            </select>
          </label>
          <label>
            <span>Status</span>
            <select value={status} onChange={(e) => setStatus(e.target.value as ShowDetail["status"])}>
              <option value="draft">Draft</option>
              <option value="published">Published</option>
            </select>
          </label>
          <label>
            <span>Slug</span>
            <input className="mono" value={slug} onChange={(e) => setSlug(e.target.value)} />
          </label>
        </div>
        <label>
          <span>Synopsis</span>
          <textarea value={synopsis} onChange={(e) => setSynopsis(e.target.value)} rows={4} />
        </label>
        <fieldset className="cats">
          <legend>Categories</legend>
          {CATEGORIES.map((c) => (
            <label key={c} className="cat">
              <input
                type="checkbox"
                checked={categories.includes(c)}
                onChange={() =>
                  setCategories((cur) => (cur.includes(c) ? cur.filter((x) => x !== c) : [...cur, c]))
                }
              />
              {c}
            </label>
          ))}
        </fieldset>
        <p>
          <button type="submit" disabled={saveShow.isPending}>
            {saveShow.isPending ? "Saving…" : "Save show"}
          </button>
        </p>
      </form>

      <h2 className="section-art">Show artwork</h2>
      <p className="hint">Poster = browse rows. Banner = featured hero. Thumbnail = search fallback.</p>
      <div className="grid3">
        {(["poster", "banner", "thumbnail"] as const).map((kind) => (
          <ArtworkSlot
            key={kind}
            kind={kind}
            current={kindOf(show.artwork, kind)}
            endpoint={`/admin/shows/${show.id}/artwork`}
            onUploaded={() => qc.invalidateQueries({ queryKey: ["show", id] })}
          />
        ))}
      </div>

      <div className="card add-row">
        <h2>Add a season</h2>
        <p className="hint">Season 0 is trailers. It will not appear as a normal season on the kids’ app.</p>
        <div className="inline-form">
          <label>
            <span>Number</span>
            <input
              type="number"
              min={0}
              value={seasonNumber}
              onChange={(e) => setSeasonNumber(Number(e.target.value))}
            />
          </label>
          <button type="button" onClick={() => addSeason.mutate()} disabled={addSeason.isPending}>
            {addSeason.isPending ? "Adding…" : "Add season"}
          </button>
        </div>
      </div>

      {show.seasons.length === 0 && <p className="hint">No seasons yet. Add one above, then add episodes.</p>}

      {show.seasons.map((season) => (
        <SeasonBlock
          key={season.id}
          season={season}
          showId={show.id}
          onError={setFormError}
          onChanged={() => qc.invalidateQueries({ queryKey: ["show", id] })}
        />
      ))}
    </div>
  );
}

function SeasonBlock({
  season,
  showId,
  onError,
  onChanged,
}: {
  season: Season;
  showId: string;
  onError: (err: unknown) => void;
  onChanged: () => void;
}) {
  return (
    <div className="card">
      <h2>{season.number === 0 ? "Trailers (season 0)" : `Season ${season.number}`}</h2>
      <NewEpisodeForm seasonId={season.id} showId={showId} onError={onError} onCreated={onChanged} />
      {season.episodes.length === 0 && <p className="hint">No episodes in this season yet.</p>}
      {season.episodes.map((ep) => (
        <EpisodeCard key={ep.id} episode={ep} onError={onError} onChanged={onChanged} />
      ))}
    </div>
  );
}

function NewEpisodeForm({
  seasonId,
  showId,
  onError,
  onCreated,
}: {
  seasonId: string;
  showId: string;
  onError: (err: unknown) => void;
  onCreated: () => void;
}) {
  const [title, setTitle] = useState("");
  const [number, setNumber] = useState(1);
  const [language, setLanguage] = useState("en");
  const [contentGroup, setContentGroup] = useState("");
  const [duration, setDuration] = useState("");
  const create = useMutation({
    mutationFn: () =>
      api<Episode>(`/admin/seasons/${seasonId}/episodes`, {
        method: "POST",
        body: JSON.stringify({
          title,
          number,
          language,
          content_group: contentGroup || `${showId.slice(0, 8)}-e${number}`,
          duration_seconds: duration ? Number(duration) : null,
          status: "draft",
        }),
      }),
    onSuccess: () => {
      setTitle("");
      setDuration("");
      setContentGroup("");
      onCreated();
    },
    onError,
  });

  return (
    <form
      className="inline-form episode-create"
      onSubmit={(e) => {
        e.preventDefault();
        create.mutate();
      }}
    >
      <label>
        <span>New episode title</span>
        <input value={title} onChange={(e) => setTitle(e.target.value)} required />
      </label>
      <label>
        <span>#</span>
        <input type="number" min={1} value={number} onChange={(e) => setNumber(Number(e.target.value))} />
      </label>
      <label>
        <span>Language</span>
        <select value={language} onChange={(e) => setLanguage(e.target.value)}>
          {LANGUAGES.map((l) => (
            <option key={l.id} value={l.id}>
              {l.label}
            </option>
          ))}
        </select>
      </label>
      <label>
        <span>Content group</span>
        <input
          className="mono"
          value={contentGroup}
          placeholder="same group = language variants"
          onChange={(e) => setContentGroup(e.target.value)}
        />
      </label>
      <label>
        <span>Duration (sec)</span>
        <input type="number" min={1} value={duration} onChange={(e) => setDuration(e.target.value)} />
      </label>
      <button type="submit" disabled={create.isPending || !title.trim()}>
        {create.isPending ? "Adding…" : "Add episode"}
      </button>
    </form>
  );
}

function EpisodeCard({
  episode,
  onError,
  onChanged,
}: {
  episode: Episode;
  onError: (err: unknown) => void;
  onChanged: () => void;
}) {
  const [title, setTitle] = useState(episode.title);
  const [language, setLanguage] = useState(episode.language);
  const [contentGroup, setContentGroup] = useState(episode.content_group);
  const [duration, setDuration] = useState(episode.duration_seconds ? String(episode.duration_seconds) : "");
  const [status, setStatus] = useState(episode.status);

  const languageLabel =
    LANGUAGES.find((l) => l.id === episode.language)?.label ?? episode.language;

  useEffect(() => {
    setTitle(episode.title);
    setLanguage(episode.language);
    setContentGroup(episode.content_group);
    setDuration(episode.duration_seconds ? String(episode.duration_seconds) : "");
    setStatus(episode.status);
  }, [episode]);

  const save = useMutation({
    mutationFn: (body: Partial<Episode>) =>
      api<Episode>(`/admin/episodes/${episode.id}`, { method: "PATCH", body: JSON.stringify(body) }),
    onSuccess: onChanged,
    onError,
  });

  return (
    <article className="episode-card">
      <div className="episode-head">
        <strong>Episode {episode.number}</strong>
        <span>{languageLabel}</span>
      </div>
      <div className="episode-fields">
        <label>
          <span>Episode title</span>
          <input
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            onBlur={() => title !== episode.title && save.mutate({ title })}
          />
        </label>
        <label>
          <span>Language</span>
          <select
            value={language}
            onChange={(e) => {
              setLanguage(e.target.value);
              save.mutate({ language: e.target.value });
            }}
          >
            {LANGUAGES.map((l) => (
              <option key={l.id} value={l.id}>
                {l.label}
              </option>
            ))}
          </select>
        </label>
        <label>
          <span>Content group</span>
          <input
            className="mono"
            value={contentGroup}
            onChange={(e) => setContentGroup(e.target.value)}
            onBlur={() => contentGroup !== episode.content_group && save.mutate({ content_group: contentGroup })}
          />
        </label>
        <label>
          <span>Duration (sec)</span>
          <input
            type="number"
            value={duration}
            onChange={(e) => setDuration(e.target.value)}
            onBlur={() => {
              const next = duration ? Number(duration) : null;
              if (next !== episode.duration_seconds) save.mutate({ duration_seconds: next });
            }}
          />
        </label>
        <label>
          <span>Status</span>
          <select
            value={status}
            onChange={(e) => {
              const next = e.target.value as Episode["status"];
              setStatus(next);
              save.mutate({ status: next });
            }}
          >
            <option value="draft">draft</option>
            <option value="published">published</option>
          </select>
        </label>
      </div>
      <div className="grid3">
        {(["poster", "banner", "thumbnail"] as const).map((kind) => (
          <ArtworkSlot
            key={kind}
            kind={kind}
            compact
            current={kindOf(episode.artwork, kind)}
            endpoint={`/admin/episodes/${episode.id}/artwork`}
            onUploaded={onChanged}
          />
        ))}
      </div>
    </article>
  );
}
