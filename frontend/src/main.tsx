import React from "react";
import ReactDOM from "react-dom/client";
import App from "./App";
import { WorkbenchProvider } from "./state/WorkbenchContext";
import "./style.css";
ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <WorkbenchProvider>
      <App />
    </WorkbenchProvider>
  </React.StrictMode>,
);
