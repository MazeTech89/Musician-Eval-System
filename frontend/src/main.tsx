import React from "react";
import ReactDOM from "react-dom/client";
import App from "./App.tsx";
import "./index.css";

// Vite's index.html contains a single <div id="root"> that React mounts into
const rootElement = document.getElementById("root");

if (!rootElement) {
  throw new Error("Root element not found");
}

// StrictMode enables extra dev-time checks (double-invoked effects, etc.)
ReactDOM.createRoot(rootElement).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
