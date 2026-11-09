export type Row = Record<string, any>;
export type Params = {
  embedding_model: string;
  language: string;
  umap: { n_neighbors: number; n_components: number; min_dist: number };
  hdbscan: { min_cluster_size: number };
  vectorizer: { ngram_range: number[]; min_df: number; max_df: number };
  representation_models: string[];
  top_n_words: number;
  name_topics: boolean;
  naming_model: string;
};
export type Job = {
  status: string;
  progress: number;
  message: string;
  error: string;
  warning: string;
  kind: string;
};
export const idleJob: Job = {
  status: "idle",
  progress: 0,
  message: "",
  error: "",
  warning: "",
  kind: "",
};
export const post = (body: unknown): RequestInit => ({
  method: "POST",
  body: JSON.stringify(body),
});
export async function api<T = any>(
  path: string,
  token: string,
  init: RequestInit = {},
): Promise<T> {
  const headers = new Headers(init.headers);
  if (token) headers.set("X-Workspace-ID", token);
  if (init.body && !(init.body instanceof FormData))
    headers.set("Content-Type", "application/json");
  const response = await fetch(`/api${path}`, { ...init, headers });
  if (!response.ok) {
    const body = await response
      .json()
      .catch(() => ({ detail: "Server nicht erreichbar." }));
    throw new Error(
      Array.isArray(body.detail)
        ? body.detail.map((e: any) => e.msg).join(" · ")
        : body.detail || "Anfrage fehlgeschlagen.",
    );
  }
  return response.json();
}
export function defaults(d: Row, model: string): Params {
  return {
    embedding_model: d.embedding_model,
    language: d.language,
    umap: {
      n_neighbors: d.n_neighbors,
      n_components: d.n_components,
      min_dist: d.min_dist,
    },
    hdbscan: { min_cluster_size: d.min_cluster_size },
    vectorizer: {
      ngram_range: d.ngram_range,
      min_df: d.min_df,
      max_df: d.max_df,
    },
    representation_models: d.representations,
    top_n_words: d.top_n_words,
    name_topics: false,
    naming_model: model,
  };
}
