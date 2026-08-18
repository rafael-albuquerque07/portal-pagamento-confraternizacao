/**
 * Ponto de entrada do PWA — decide qual página renderizar (participante ou admin)
 * e registra o service worker.
 */
import { renderPaginaAdmin } from "./pages/admin";
import { renderPaginaParticipante } from "./pages/participante";

const app = document.querySelector<HTMLDivElement>("#app")!;

function rotear(): void {
  const path = window.location.pathname;

  if (path.startsWith("/admin")) {
    renderPaginaAdmin(app);
    return;
  }

  // Rota padrão: /:slug (link único do participante)
  const slug = path.replace(/^\//, "");
  renderPaginaParticipante(app, slug);
}

rotear();

if ("serviceWorker" in navigator) {
  window.addEventListener("load", () => {
    navigator.serviceWorker.register("/src/sw.ts", { type: "module" }).catch((erro) => {
      console.error("Falha ao registrar o service worker:", erro);
    });
  });
}
