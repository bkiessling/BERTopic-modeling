import {
  createContext,
  useContext,
  useCallback,
  useEffect,
  useRef,
  useState,
} from "react";
import type { ReactNode } from "react";
import { api, post, defaults, idleJob } from "../api";
import type { Job, Params, Row } from "../api";
const options = (values: string[]) =>
  values.map((value) => ({ value, label: value }));
const message = (error: unknown) =>
  error instanceof Error
    ? error.message
    : "Ein unerwarteter Fehler ist aufgetreten.";
function useWorkbenchState() {
  const [token, setToken] = useState(""),
    [caps, setCaps] = useState<Row | null>(null),
    [step, setStep] = useState(0);
  const [uploaded, setUploaded] = useState<Row | null>(null),
    [cleaned, setCleaned] = useState<Row | null>(null),
    [params, setParams] = useState<Params | null>(null),
    [result, setResult] = useState<Row | null>(null);
  const [job, setJob] = useState<Job>(idleJob),
    [busy, setBusy] = useState(""),
    [error, setError] = useState(""),
    [notice, setNotice] = useState("");
  const [textCols, setTextCols] = useState<string[]>([]),
    [idCol, setIdCol] = useState("ID generieren"),
    [sample, setSample] = useState(100),
    [stopwords, setStopwords] = useState(""),
    [file, setFile] = useState<File | null>(null);
  const [resultTab, setResultTab] = useState("topics"),
    [chartKind, setChartKind] = useState("network"),
    [chart, setChart] = useState<any>(null),
    [chartError, setChartError] = useState("");
  const [selectedTopics, setSelectedTopics] = useState<number[]>([]),
    [method, setMethod] = useState("umap"),
    [revision, setRevision] = useState(0),
    [documents, setDocuments] = useState<Row | null>(null);
  const [search, setSearch] = useState(""),
    [page, setPage] = useState(0),
    [threshold, setThreshold] = useState(0.05),
    [settings, setSettings] = useState(false),
    [namingModel, setNamingModel] = useState("gpt-4.1-mini");
  const [topWords, setTopWords] = useState(5),
    [documentTopic, setDocumentTopic] = useState(""),
    [documentSort, setDocumentSort] = useState("ID"),
    [descending, setDescending] = useState(false),
    [pendingNaming, setPendingNaming] = useState(false);
  const fileInput = useRef<HTMLInputElement>(null),
    completed = useRef(false),
    initializing = useRef<Promise<Row> | null>(null);
  const active = ["queued", "running"].includes(job.status),
    blocked = active || !!busy;
  const loadResults = useCallback(async (id: string, resetView = true) => {
    const value = await api("/results", id);
    setResult(value);
    if (resetView) {
      setPage(0);
      setDocumentTopic("");
      setDocuments(null);
      setSelectedTopics(
        (value.topics as Row[])
          .filter((t) => t.Thema !== -1)
          .slice(0, 4)
          .map((t) => t.Thema),
      );
    }
    setRevision((v) => v + 1);
    return value;
  }, []);
  useEffect(() => {
    let live = true;
    if (!initializing.current)
      initializing.current = (async () => {
        let capability = await api("/capabilities", "");
        let id = localStorage.getItem("themenstudio-workspace") || "",
          restored: Row | null = null;
        if (id) {
          try {
            restored = await api("/workspace", id);
          } catch {
            id = "";
          }
        }
        if (!id) {
          id = (await api("/workspaces", "", { method: "POST" })).id;
          localStorage.setItem("themenstudio-workspace", id);
        }
        capability = await api("/capabilities", id);
        return { capability, id, restored };
      })();
    initializing.current
      .then(async ({ capability, id, restored }) => {
        if (!live) return;
        setCaps(capability);
        setToken(id);
        setNamingModel(capability.default_naming_model);
        if (restored?.import_result) {
          setUploaded(restored.import_result);
          setTextCols(restored.text_columns || []);
          setIdCol(restored.id_column || "ID generieren");
          setSample(restored.preprocessing?.sample_percentage || 100);
          setStopwords(restored.preprocessing?.custom_stopwords || "");
        }
        if (restored?.clean_result) {
          setCleaned(restored.clean_result);
          setParams(
            defaults(
              restored.clean_result.defaults,
              capability.default_naming_model,
            ),
          );
        }
        if (restored?.has_results) {
          const previous = await loadResults(id);
          if (live) {
            setParams(previous.parameters);
            setNamingModel(
              previous.naming.model || previous.parameters.naming_model,
            );
            setStep(2);
          }
        }
        if (restored?.job) setJob(restored.job);
      })
      .catch((e) => {
        if (live) setError(message(e));
      });
    return () => {
      live = false;
    };
  }, [loadResults]);
  useEffect(() => {
    if (!active || !token) return;
    let live = true;
    completed.current = false;
    const timer = setInterval(async () => {
      try {
        const next = await api<Job>("/job", token);
        if (!live) return;
        if (next.status === "completed" && !completed.current) {
          completed.current = true;
          await loadResults(token);
          if (!live) return;
          setStep(2);
          setNotice(next.warning || "");
        }
        setJob(next);
      } catch (e) {
        if (live) setError(message(e));
      }
    }, 750);
    return () => {
      live = false;
      clearInterval(timer);
    };
  }, [active, token, loadResults]);
  useEffect(() => {
    if (!result || step !== 2) return;
    let live = true;
    setDocuments(null);
    const timer = setTimeout(() => {
      api(
        `/documents?page=${page}&search=${encodeURIComponent(search)}${documentTopic !== "" ? `&topic=${encodeURIComponent(documentTopic)}` : ""}&sort=${encodeURIComponent(documentSort)}&descending=${descending}`,
        token,
      )
        .then((data) => {
          if (live) setDocuments(data);
        })
        .catch((e) => {
          if (live) setError(message(e));
        });
    }, 200);
    return () => {
      live = false;
      clearTimeout(timer);
    };
  }, [
    result,
    step,
    page,
    search,
    token,
    revision,
    documentTopic,
    documentSort,
    descending,
  ]);
  useEffect(() => {
    if (!result || step !== 2 || resultTab !== "charts") return;
    let live = true;
    setChart(null);
    setChartError("");
    if (chartKind === "bars" && !selectedTopics.length) return;
    api(
      `/charts/${chartKind}?topics=${selectedTopics.join(",")}&method=${method}&top_words=${topWords}`,
      token,
    )
      .then((data) => {
        if (live) setChart(data);
      })
      .catch((e) => {
        if (live) setChartError(message(e));
      });
    return () => {
      live = false;
    };
  }, [
    result,
    step,
    resultTab,
    chartKind,
    selectedTopics,
    method,
    topWords,
    token,
    revision,
  ]);
  useEffect(() => {
    if (!settings) {
      setPendingNaming(false);
      return;
    }
    const escape = (event: KeyboardEvent) => {
      if (event.key === "Escape") setSettings(false);
      if (event.key === "Tab") {
        const items = document.querySelectorAll<HTMLElement>(
          "[role=dialog] input:not(:disabled),[role=dialog] button:not(:disabled),[role=dialog] select:not(:disabled),[role=dialog] a[href]",
        );
        const first = items[0],
          last = items[items.length - 1];
        if (event.shiftKey && document.activeElement === first) {
          event.preventDefault();
          last?.focus();
        } else if (!event.shiftKey && document.activeElement === last) {
          event.preventDefault();
          first?.focus();
        }
      }
    };
    document.addEventListener("keydown", escape);
    return () => document.removeEventListener("keydown", escape);
  }, [settings]);
  function requestNaming(enabled: boolean) {
    if (enabled && !caps?.key_present) {
      setPendingNaming(true);
      setSettings(true);
    } else change({ name_topics: enabled });
  }
  async function saveSessionKey(key: string) {
    await api("/openai/key", token, post({ key }));
    setCaps(await api("/capabilities", token));
    if (pendingNaming) change({ name_topics: true });
    setPendingNaming(false);
  }
  async function perform(name: string, task: () => Promise<void>) {
    setBusy(name);
    setError("");
    try {
      await task();
    } catch (e) {
      setError(message(e));
    } finally {
      setBusy("");
    }
  }
  async function upload(next: File, delimiter?: string) {
    await perform("upload", async () => {
      const form = new FormData();
      form.append("file", next);
      if (delimiter) form.append("delimiter", delimiter);
      const data = await api("/import", token, { method: "POST", body: form });
      setUploaded(data);
      setFile(next);
      setTextCols([]);
      setIdCol("ID generieren");
      setCleaned(null);
      setResult(null);
      setParams(null);
      setJob(idleJob);
      setNotice("");
    });
  }
  async function clean() {
    await perform("clean", async () => {
      const data = await api(
        "/clean",
        token,
        post({
          text_columns: textCols,
          id_column: idCol,
          sample_percentage: sample,
          custom_stopwords: stopwords,
        }),
      );
      setCleaned(data);
      setParams(defaults(data.defaults, namingModel));
      setResult(null);
      setJob(idleJob);
      setNotice("");
    });
  }
  function change(update: Partial<Params>) {
    setParams((old) => (old ? { ...old, ...update } : old));
  }
  async function startJob(path: string, body: unknown = {}) {
    await perform("job", async () => {
      if (path === "/train") {
        const health = await api("/health", token);
        if (health.api_contract !== "bertopic-proportions-v1") {
          throw new Error(
            "Das laufende Backend ist veraltet. Alten Server beenden und neu starten; alternativ npm start -- --port 8001 verwenden.",
          );
        }
      }
      completed.current = false;
      setJob(await api<Job>(path, token, post(body)));
      setNotice("");
    });
  }
  async function renameTopic(topic: number, label: string) {
    await perform("label", async () => {
      await api("/topics/label", token, post({ topic, label }));
      await loadResults(token, false);
      setNotice("Themenname gespeichert.");
    });
  }
  async function download() {
    await perform("export", async () => {
      const response = await fetch("/api/export", {
        headers: { "X-Workspace-ID": token },
      });
      if (!response.ok) throw new Error("Export konnte nicht erstellt werden.");
      const url = URL.createObjectURL(await response.blob());
      const link = document.createElement("a");
      link.href = url;
      link.download = "topic-modeling-results.zip";
      link.click();
      setTimeout(() => URL.revokeObjectURL(url), 1000);
    });
  }
  const modelOptions: Row[] = (caps?.models || []).filter((m: Row) =>
    m.languages.includes(params?.language || "Deutsch"),
  );
  const topics: Row[] = result?.topics || [],
    keywords: Row[] = result?.keywords || [];
  const idPreviewColumn =
    idCol === "ID generieren"
      ? textCols.includes("ID")
        ? "ID (generiert)"
        : "ID"
      : idCol;
  const sourcePreview: Row[] = (uploaded?.preview || []).map((row: Row) => {
    const selected: Row = {
      [idPreviewColumn]: idCol === "ID generieren" ? "" : row[idCol],
    };
    for (const column of textCols) selected[column] = row[column];
    return selected;
  });
  const invalid: string[] = [];
  if (params && cleaned) {
    if (cleaned.rows < 4)
      invalid.push("Mindestens vier bereinigte Texte erforderlich.");
    if (params.umap.n_neighbors >= cleaned.rows)
      invalid.push("Nachbarn müssen unter der Textanzahl liegen.");
    if (params.umap.n_components > cleaned.rows - 2)
      invalid.push(
        "Dimensionen müssen mindestens zwei unter der Textanzahl liegen.",
      );
    if (params.hdbscan.min_cluster_size > cleaned.rows)
      invalid.push("Clustergröße überschreitet die Textanzahl.");
    if (params.vectorizer.min_df > params.vectorizer.max_df)
      invalid.push("Minimale Häufigkeit überschreitet das Maximum.");
  }

  return {
    token,
    setToken,
    caps,
    setCaps,
    step,
    setStep,
    uploaded,
    setUploaded,
    cleaned,
    setCleaned,
    params,
    setParams,
    result,
    setResult,
    job,
    setJob,
    busy,
    setBusy,
    error,
    setError,
    notice,
    setNotice,
    textCols,
    setTextCols,
    idCol,
    setIdCol,
    sample,
    setSample,
    stopwords,
    setStopwords,
    file,
    setFile,
    resultTab,
    setResultTab,
    chartKind,
    setChartKind,
    chart,
    setChart,
    chartError,
    setChartError,
    selectedTopics,
    setSelectedTopics,
    method,
    setMethod,
    revision,
    setRevision,
    documents,
    setDocuments,
    search,
    setSearch,
    page,
    setPage,
    threshold,
    setThreshold,
    settings,
    setSettings,
    namingModel,
    setNamingModel,
    fileInput,
    active,
    blocked,
    loadResults,
    perform,
    upload,
    clean,
    change,
    startJob,
    download,
    renameTopic,
    modelOptions,
    topics,
    keywords,
    invalid,
    idPreviewColumn,
    sourcePreview,
    options,
    topWords,
    setTopWords,
    documentTopic,
    setDocumentTopic,
    documentSort,
    setDocumentSort,
    descending,
    setDescending,
    requestNaming,
    saveSessionKey,
  };
}
const Context = createContext<ReturnType<typeof useWorkbenchState> | null>(
  null,
);
export function WorkbenchProvider({ children }: { children: ReactNode }) {
  return (
    <Context.Provider value={useWorkbenchState()}>{children}</Context.Provider>
  );
}
export function useWorkbench() {
  const state = useContext(Context);
  if (!state) throw new Error("WorkbenchProvider fehlt");
  return state;
}
