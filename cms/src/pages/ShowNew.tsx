import { useMutation } from "@tanstack/react-query";
import { FormEvent, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { api } from "../api";
import { ErrorBanner } from "../components/States";
import { CATEGORIES, SECTIONS, type ShowDetail } from "../types";

export function ShowNewPage() {
  const nav = useNavigate();
  const [title, setTitle] = useState("");
  const [slug, setSlug] = useState("");
  const [synopsis, setSynopsis] = useState("");
  const [section, setSection] = useState("");
  const [categories, setCategories] = useState<string[]>([]);
  const [error, setError] = useState<unknown>(null);

  const create = useMutation({
    mutationFn: () =>
      api<ShowDetail>("/admin/shows", {
        method: "POST",
        body: JSON.stringify({
          title,
          slug: slug || title.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, ""),
          synopsis,
          section: section || null,
          categories,
          status: "draft",
        }),
      }),
    onSuccess: (show) => nav(`/shows/${show.id}`),
    onError: setError,
  });

  function onSubmit(e: FormEvent) {
    e.preventDefault();
    create.mutate();
  }

  return (
    <div className="page">
      <p>
        <Link to="/shows" className="back">
          ← All shows
        </Link>
      </p>
      <header className="page-head">
        <div>
          <p className="kicker">New title</p>
          <h1>Add a show</h1>
          <p className="lede">Starts as a draft. Hang artwork and episodes on the next screen, then publish it.</p>
        </div>
      </header>
      {error ? <ErrorBanner error={error} /> : null}
      <form className="card" onSubmit={onSubmit}>
        <div className="grid2">
          <label>
            <span>Title</span>
            <input value={title} onChange={(e) => setTitle(e.target.value)} required />
          </label>
          <label>
            <span>Web name (slug)</span>
            <input
              className="mono"
              value={slug}
              placeholder="auto from title"
              onChange={(e) => setSlug(e.target.value)}
            />
          </label>
          <label>
            <span>Section</span>
            <select value={section} onChange={(e) => setSection(e.target.value)}>
              <option value="">— none yet —</option>
              {SECTIONS.map((s) => (
                <option key={s.id} value={s.id}>
                  {s.label}
                </option>
              ))}
            </select>
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
          <button type="submit" disabled={create.isPending || !title.trim()}>
            {create.isPending ? "Creating…" : "Create show"}
          </button>
        </p>
      </form>
    </div>
  );
}
