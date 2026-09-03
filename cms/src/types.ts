export type Role = "editor" | "admin";

export type Artwork = {
  id: string;
  kind: "poster" | "banner" | "thumbnail";
  url: string;
  width: number;
  height: number;
  byte_size: number;
};

export type Episode = {
  id: string;
  season_id: string;
  show_id: string;
  external_id: string | null;
  title: string;
  number: number;
  duration_seconds: number | null;
  language: string;
  content_group: string;
  status: "draft" | "published";
  artwork: Artwork[];
};

export type Season = {
  id: string;
  show_id: string;
  number: number;
  episode_count: number;
  episodes: Episode[];
};

export type Show = {
  id: string;
  title: string;
  slug: string;
  synopsis: string;
  section: string | null;
  categories: string[];
  status: "draft" | "published";
  episode_count: number;
  artwork: Artwork[];
};

export type ShowDetail = Show & { seasons: Season[] };

export type ShowList = {
  items: Show[];
  total: number;
  page: number;
  page_size: number;
};

export type Issue = {
  severity: string;
  code: string;
  message: string;
  how_to_fix: string;
  show_id: string | null;
  show_title: string | null;
  episode_id: string | null;
  episode_title: string | null;
};

export type ValidationReport = {
  can_publish: boolean;
  blocking: Issue[];
  warnings: Issue[];
  groups: Record<string, Issue[]>;
};

export type PublishRun = {
  id: string;
  actor_email: string;
  started_at: string;
  finished_at: string | null;
  outcome: string;
  show_count: number;
  episode_count: number;
  catalogue_key: string | null;
  error: string | null;
  notes?: Record<string, unknown> | null;
};

export const SPECS: Record<string, { label: string; size: string; aspect: string }> = {
  poster: { label: "Poster", size: "600 × 900 px", aspect: "2:3 — tall, used on browse rows" },
  banner: { label: "Banner", size: "1280 × 720 px", aspect: "16:9 — wide, used on the featured hero" },
  thumbnail: { label: "Thumbnail", size: "640 × 360 px", aspect: "16:9 — used on episode lists" },
};

export const SECTIONS = [
  { id: "featured", label: "Featured" },
  { id: "series", label: "Series" },
  { id: "minisodes", label: "Minisodes" },
  { id: "songs", label: "Songs" },
];

export const LANGUAGES = [
  { id: "en", label: "English" },
  { id: "hi", label: "Hindi" },
];

export const CATEGORIES = [
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
