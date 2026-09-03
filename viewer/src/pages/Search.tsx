import { useQuery } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { searchCatalogue } from "../api";
import { PosterCard } from "../components/PosterCard";

const CATEGORIES = [
  "adventure",
  "folk",
  "friendship",
  "india",
  "language",
  "learning",
  "maths",
  "music",
  "nature",
  "reading",
  "science",
  "singalong",
  "stories",
  "travel",
  "values",
];

export function SearchPage() {
  const [params, setParams] = useSearchParams();
  const q = params.get("q") ?? "";
  const category = params.get("category") ?? "";
  const language = params.get("language") ?? "";
  const [typed, setTyped] = useState(q);

  useEffect(() => {
    setTyped(q);
  }, [q]);

  useEffect(() => {
    const id = window.setTimeout(() => {
      const next = new URLSearchParams(params);
      if (typed) next.set("q", typed);
      else next.delete("q");
      if (next.toString() !== params.toString()) setParams(next, { replace: true });
    }, 300);
    return () => window.clearTimeout(id);
  }, [typed, params, setParams]);

  const query = useQuery({
    queryKey: ["search", q, category, language],
    queryFn: () => {
      const p = new URLSearchParams();
      if (q) p.set("q", q);
      if (category) p.set("category", category);
      if (language) p.set("language", language);
      return searchCatalogue(p);
    },
  });

  function set(key: string, value: string) {
    const next = new URLSearchParams(params);
    if (value) next.set(key, value);
    else next.delete(key);
    setParams(next);
  }

  return (
    <div className="page">
      <h1>Search</h1>
      <div className="filters">
        <input
          placeholder="Titles, episodes, categories"
          value={typed}
          onChange={(e) => setTyped(e.target.value)}
          autoFocus
        />
        <select value={category} onChange={(e) => set("category", e.target.value)}>
          <option value="">All categories</option>
          {CATEGORIES.map((c) => (
            <option key={c} value={c}>
              {c}
            </option>
          ))}
        </select>
        <select value={language} onChange={(e) => set("language", e.target.value)}>
          <option value="">All languages</option>
          <option value="en">English</option>
          <option value="hi">Hindi</option>
        </select>
      </div>
      {query.isLoading && <p>Looking…</p>}
      {query.isError && <p>{query.error.message}</p>}
      {query.data && query.data.results.length === 0 && (
        <div className="empty">
          <h2>No matches</h2>
          <p>Try a shorter word, or clear a filter.</p>
        </div>
      )}
      <div className="grid">
        {query.data?.results.map((show) => (
          <PosterCard key={show.id} show={show} />
        ))}
      </div>
    </div>
  );
}
