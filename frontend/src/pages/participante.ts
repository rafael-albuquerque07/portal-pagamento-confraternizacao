/**
 * Página do participante — lista as 4 parcelas e permite pagar via Pix.
 * Consome GET /api/participante/{slug}/pagamentos e /pix/{mes}.
 */
import { renderQrCodePix } from "../components/qrcode-pix";

interface PagamentoParticipante {
  mes_referencia: string;
  valor_esperado: number;
  status: string;
}

interface PixResponse {
  qr_code_base64: string;
  payload_copia_cola: string;
}

export function renderPaginaParticipante(container: HTMLElement, slug: string): void {
  garantirEstilos();
  carregarPagamentos(container, slug);
}

async function carregarPagamentos(container: HTMLElement, slug: string): Promise<void> {
  container.innerHTML = `<main class="pagina-participante"><h1>Minhas parcelas</h1><p>Carregando…</p></main>`;

  let resposta: Response;
  try {
    resposta = await fetch(`/api/participante/${encodeURIComponent(slug)}/pagamentos`);
  } catch {
    renderErro(container, "Não foi possível conectar ao servidor.");
    return;
  }

  if (resposta.status === 404) {
    renderErro(container, "Participante não encontrado. Confira o link recebido.");
    return;
  }

  if (!resposta.ok) {
    renderErro(container, `Erro inesperado ao carregar suas parcelas (${resposta.status}).`);
    return;
  }

  const parcelas: PagamentoParticipante[] = await resposta.json();
  renderParcelas(container, slug, parcelas);
}

function renderErro(container: HTMLElement, mensagem: string): void {
  container.innerHTML = `
    <main class="pagina-participante">
      <h1>Minhas parcelas</h1>
      <p class="erro">${escapeHtml(mensagem)}</p>
    </main>
  `;
}

function renderParcelas(container: HTMLElement, slug: string, parcelas: PagamentoParticipante[]): void {
  const itens = parcelas
    .map(
      (parcela) => `
        <li class="parcela status-${escapeHtml(parcela.status)}">
          <span class="mes">${escapeHtml(parcela.mes_referencia)}</span>
          <span class="valor">R$ ${parcela.valor_esperado.toFixed(2)}</span>
          <span class="status">${escapeHtml(parcela.status)}</span>
        </li>
      `,
    )
    .join("");

  container.innerHTML = `
    <main class="pagina-participante">
      <h1>Minhas parcelas</h1>
      <ul class="lista-parcelas">${itens}</ul>
      <div id="area-pix"></div>
    </main>
  `;

  const primeiraPendente = parcelas.find((parcela) => parcela.status === "pendente");
  if (primeiraPendente) {
    carregarPix(container, slug, primeiraPendente.mes_referencia);
  }
}

async function carregarPix(container: HTMLElement, slug: string, mes: string): Promise<void> {
  const areaPix = container.querySelector<HTMLDivElement>("#area-pix")!;
  areaPix.innerHTML = "<p>Carregando QR Code Pix…</p>";

  let resposta: Response;
  try {
    resposta = await fetch(`/api/participante/${encodeURIComponent(slug)}/pix/${encodeURIComponent(mes)}`);
  } catch {
    areaPix.innerHTML = `<p class="erro">Não foi possível carregar o QR Code Pix.</p>`;
    return;
  }

  if (!resposta.ok) {
    areaPix.innerHTML = `<p class="erro">O QR Code Pix desta parcela ainda não está disponível.</p>`;
    return;
  }

  const pix: PixResponse = await resposta.json();
  renderQrCodePix(areaPix, pix.qr_code_base64, pix.payload_copia_cola);
}

function escapeHtml(texto: string): string {
  const div = document.createElement("div");
  div.textContent = texto;
  return div.innerHTML;
}

function garantirEstilos(): void {
  if (document.getElementById("estilos-pagina-participante")) return;

  const style = document.createElement("style");
  style.id = "estilos-pagina-participante";
  style.textContent = `
    .pagina-participante { font-family: system-ui, sans-serif; max-width: 480px; margin: 2rem auto; padding: 0 1rem; }
    .pagina-participante .lista-parcelas { list-style: none; padding: 0; }
    .pagina-participante .parcela { display: flex; justify-content: space-between; gap: 0.5rem; padding: 0.75rem; border: 1px solid #ccc; border-radius: 6px; margin-bottom: 0.5rem; }
    .pagina-participante .parcela .status { font-weight: 600; }
    .pagina-participante .status-pago .status { color: #1a7f37; }
    .pagina-participante .status-pendente .status { color: #9a6700; }
    .pagina-participante .status-falhou .status { color: #cf222e; }
    .pagina-participante .erro { color: #cf222e; }
    .qrcode-pix { text-align: center; margin-top: 1.5rem; }
    .qrcode-pix img { max-width: 240px; width: 100%; }
    .qrcode-pix button { margin-top: 0.75rem; }
    .qrcode-pix .msg-copiado { color: #1a7f37; }
    .qrcode-pix .msg-copiado.erro { color: #cf222e; }
  `;
  document.head.appendChild(style);
}
