/**
 * Painel administrativo — visão geral de participantes x parcelas.
 * Consome GET /api/admin/dashboard (autenticado via HTTP Basic).
 */

interface ParcelaDashboard {
  mes_referencia: string;
  status: string;
  data_confirmacao: string | null;
}

interface ParticipanteDashboard {
  nome: string;
  cpf_mascarado: string;
  parcelas: ParcelaDashboard[];
}

// Credencial mantida só em memória — nunca em localStorage/sessionStorage.
// Some ao recarregar a página; o admin precisa entrar de novo.
let credencialBasic: string | null = null;

export function renderPaginaAdmin(container: HTMLElement): void {
  garantirEstilos();

  if (credencialBasic) {
    carregarDashboard(container);
  } else {
    renderLogin(container);
  }
}

function renderLogin(container: HTMLElement, erro?: string): void {
  container.innerHTML = `
    <main class="painel-admin">
      <h1>Painel administrativo</h1>
      <form id="form-login">
        <label for="senha-admin">Senha</label>
        <input type="password" id="senha-admin" name="senha" required autofocus />
        <button type="submit">Entrar</button>
      </form>
      ${erro ? `<p class="erro">${escapeHtml(erro)}</p>` : ""}
    </main>
  `;

  const form = container.querySelector<HTMLFormElement>("#form-login")!;
  form.addEventListener("submit", (evento) => {
    evento.preventDefault();
    const senha = container.querySelector<HTMLInputElement>("#senha-admin")!.value;
    credencialBasic = `Basic ${btoa(`admin:${senha}`)}`;
    carregarDashboard(container);
  });
}

async function carregarDashboard(container: HTMLElement): Promise<void> {
  container.innerHTML = `<main class="painel-admin"><h1>Painel administrativo</h1><p>Carregando…</p></main>`;

  let resposta: Response;
  try {
    resposta = await fetch("/api/admin/dashboard", {
      headers: { Authorization: credencialBasic! },
    });
  } catch {
    renderLogin(container, "Não foi possível conectar ao servidor.");
    return;
  }

  if (resposta.status === 401) {
    credencialBasic = null;
    renderLogin(container, "Senha incorreta.");
    return;
  }

  if (!resposta.ok) {
    credencialBasic = null;
    renderLogin(container, `Erro inesperado ao carregar o painel (${resposta.status}).`);
    return;
  }

  const participantes: ParticipanteDashboard[] = await resposta.json();
  renderTabela(container, participantes);
}

function renderTabela(container: HTMLElement, participantes: ParticipanteDashboard[]): void {
  const meses = Array.from(
    new Set(participantes.flatMap((participante) => participante.parcelas.map((parcela) => parcela.mes_referencia))),
  ).sort();

  const linhas = participantes
    .map((participante) => {
      const parcelasPorMes = new Map(participante.parcelas.map((parcela) => [parcela.mes_referencia, parcela]));
      const celulas = meses
        .map((mes) => {
          const status = parcelasPorMes.get(mes)?.status ?? "—";
          return `<td class="status-${escapeHtml(status)}">${escapeHtml(status)}</td>`;
        })
        .join("");
      return `
        <tr>
          <td>${escapeHtml(participante.nome)}</td>
          <td>${escapeHtml(participante.cpf_mascarado)}</td>
          ${celulas}
        </tr>
      `;
    })
    .join("");

  container.innerHTML = `
    <main class="painel-admin">
      <h1>Painel administrativo</h1>
      ${
        participantes.length === 0
          ? "<p>Nenhum participante cadastrado ainda.</p>"
          : `
            <table>
              <thead>
                <tr>
                  <th>Nome</th>
                  <th>CPF</th>
                  ${meses.map((mes) => `<th>${escapeHtml(mes)}</th>`).join("")}
                </tr>
              </thead>
              <tbody>${linhas}</tbody>
            </table>
          `
      }
      <button id="btn-sair" type="button">Sair</button>
    </main>
  `;

  container.querySelector<HTMLButtonElement>("#btn-sair")!.addEventListener("click", () => {
    credencialBasic = null;
    renderLogin(container);
  });
}

function escapeHtml(texto: string): string {
  const div = document.createElement("div");
  div.textContent = texto;
  return div.innerHTML;
}

function garantirEstilos(): void {
  if (document.getElementById("estilos-painel-admin")) return;

  const style = document.createElement("style");
  style.id = "estilos-painel-admin";
  style.textContent = `
    .painel-admin { font-family: system-ui, sans-serif; max-width: 900px; margin: 2rem auto; padding: 0 1rem; }
    .painel-admin table { width: 100%; border-collapse: collapse; margin-top: 1rem; }
    .painel-admin th, .painel-admin td { border: 1px solid #ccc; padding: 0.5rem 0.75rem; text-align: left; }
    .painel-admin td[class^="status-"] { font-weight: 600; }
    .painel-admin td.status-pago { color: #1a7f37; }
    .painel-admin td.status-pendente { color: #9a6700; }
    .painel-admin td.status-falhou { color: #cf222e; }
    .painel-admin .erro { color: #cf222e; }
    .painel-admin button { margin-top: 1rem; }
  `;
  document.head.appendChild(style);
}
