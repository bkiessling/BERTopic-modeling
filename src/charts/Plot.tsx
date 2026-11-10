import { useState, useEffect, useRef } from "react";
export function Plot({ figure }: { figure: any }) {
  const ref = useRef<HTMLDivElement>(null);
  const [error, setError] = useState("");
  useEffect(() => {
    let disposed = false;
    let engine: any;
    const target = ref.current;
    import("plotly.js-dist-min")
      .then(async (m) => {
        engine = m.default;
        if (disposed || !target) return;
        await engine.newPlot(
          target,
          figure.data,
          { ...figure.layout, autosize: true, width: undefined },
          {
            responsive: true,
            displaylogo: false,
            toImageButtonOptions: { format: "png", scale: 2 },
          },
        );
        if (disposed) engine.purge(target);
      })
      .catch(() => {
        if (!disposed) setError("Diagramm konnte nicht geladen werden.");
      });
    return () => {
      disposed = true;
      if (engine && target) engine.purge(target);
    };
  }, [figure]);
  return error ? (
    <p className="error-text">{error}</p>
  ) : (
    <div
      className="plot"
      ref={ref}
      aria-label="Interaktives Ergebnisdiagramm"
    />
  );
}
