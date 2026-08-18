/**
 * Componente de exibição do QR Code Pix + botão "Copiar código".
 */
export function renderQrCodePix(container: HTMLElement, qrCodeBase64: string, payloadCopiaECola: string): void {
  container.innerHTML = `
    <div class="qrcode-pix">
      <img src="data:image/png;base64,${qrCodeBase64}" alt="QR Code Pix" />
      <button type="button" id="btn-copiar-pix">Copiar código Pix</button>
      <p class="msg-copiado" id="msg-copiado" hidden></p>
    </div>
  `;

  const botao = container.querySelector<HTMLButtonElement>("#btn-copiar-pix")!;
  const mensagem = container.querySelector<HTMLParagraphElement>("#msg-copiado")!;

  botao.addEventListener("click", async () => {
    try {
      await navigator.clipboard.writeText(payloadCopiaECola);
      mensagem.textContent = "Código copiado!";
      mensagem.classList.remove("erro");
    } catch {
      mensagem.textContent = "Não foi possível copiar automaticamente. Copie o código manualmente.";
      mensagem.classList.add("erro");
    }
    mensagem.hidden = false;
  });
}
