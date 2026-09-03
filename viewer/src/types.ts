export type Artwork = Partial<Record<"poster" | "banner" | "thumbnail", string>>;

export type CatalogueEpisode = {
  content_group: string;
  title: string;
  titles_by_language?: Record<string, string>;
  episode_number: number;
  duration_seconds: number | null;
  languages: string[];
  artwork: Artwork;
  playback_url?: string;
  playback_by_language?: Record<string, string>;
};

export type CatalogueSeason = {
  number: number;
  episodes: CatalogueEpisode[];
};

export type CatalogueShow = {
  id: string;
  slug: string;
  title: string;
  synopsis: string;
  categories: string[];
  section: string;
  artwork: Artwork;
  playback_url?: string;
  seasons: CatalogueSeason[];
  trailers: CatalogueEpisode[];
};

export type CatalogueSection = {
  id: string;
  title: string;
  shows: CatalogueShow[];
};

export type Catalogue = {
  published_at: string | null;
  run_id: string | null;
  sections: CatalogueSection[];
};

export type SearchResponse = {
  q: string | null;
  category: string | null;
  language: string | null;
  section: string | null;
  results: CatalogueShow[];
};
