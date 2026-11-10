import React from "react";
import ReactDOM from "react-dom/client";
import App from "./App";
import { WorkbenchProvider } from "./context/WorkbenchContext";
import "./App.css";
ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <WorkbenchProvider>
      <App />
    </WorkbenchProvider>
  </React.StrictMode>,
);
