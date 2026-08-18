/**
 * Página do participante — lista as 4 parcelas e permite pagar via Pix.
 * TODO: consumir GET /api/participante/{slug}/pagamentos e /pix/{mes}.
 */
export function renderPaginaParticipante(container: HTMLElement, slug: string): void {
  container.innerHTML = `
    <main>
      <h1>Minhas parcelas</h1>
      <p>Participante: <code>${slug}</code></p>
      <p>Em construção.</p>
    </main>
  `;
}
