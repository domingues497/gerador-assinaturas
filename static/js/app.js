/* Funções compartilhadas: pré-visualização ao vivo, copiar assinatura/HTML, testar imagem. */

function atualizarPreview() {
  const form = document.getElementById("form-assinatura");
  const previewBox = document.getElementById("preview-assinatura");
  if (!form || !previewBox) return;

  const dados = new FormData(form);
  fetch(window.PREVIEW_URL, { method: "POST", body: dados })
    .then((resp) => resp.json())
    .then((data) => {
      if (data.erro) {
        previewBox.innerHTML = `<p class="text-danger mb-0">${data.erro}</p>`;
      } else {
        previewBox.innerHTML = data.html || '<p class="text-muted mb-0">Selecione um colaborador e um modelo para pré-visualizar.</p>';
      }
    })
    .catch(() => {
      previewBox.innerHTML = '<p class="text-danger mb-0">Não foi possível atualizar a pré-visualização.</p>';
    });
}


async function enviarBannerSelecionado() {
  const input = document.getElementById("banner_arquivo");
  const urlInput = document.getElementById("banner_url");
  const status = document.getElementById("banner-upload-status");
  if (!input || !urlInput || !status || !input.files || !input.files.length) return;
  const arquivo = input.files[0];
  if (arquivo.size > 8 * 1024 * 1024) {
    status.textContent = "O arquivo excede o limite de 8 MB.";
    status.className = "small mt-1 text-danger";
    input.value = "";
    return;
  }
  const dados = new FormData();
  dados.append("banner_arquivo", arquivo);
  status.textContent = "Enviando banner...";
  status.className = "small mt-1 text-muted";
  try {
    const resp = await fetch(window.BANNER_UPLOAD_URL || "/assinaturas/upload-banner", { method: "POST", body: dados });
    const data = await resp.json();
    if (!resp.ok || !data.ok) throw new Error(data.erro || "Não foi possível enviar o banner.");
    urlInput.value = data.url;
    status.textContent = "Banner carregado para pré-visualização. Para uso externo no Outlook, publique a imagem em HTTPS.";
    status.className = "small mt-1 text-success";
    atualizarPreview();
  } catch (err) {
    status.textContent = err.message || "Falha ao enviar banner.";
    status.className = "small mt-1 text-danger";
  }
}

function ligarAtualizacaoAutomatica() {
  const form = document.getElementById("form-assinatura");
  if (!form) return;
  form.addEventListener("input", debounce(atualizarPreview, 350));
  form.addEventListener("change", (event) => {
    if (event.target && event.target.id === "banner_arquivo") {
      enviarBannerSelecionado();
      return;
    }
    atualizarPreview();
  });
  atualizarPreview();
}

function debounce(fn, wait) {
  let t;
  return (...args) => {
    clearTimeout(t);
    t = setTimeout(() => fn(...args), wait);
  };
}

function mostrarStatusCopia(elementoId, mensagem, sucesso = true) {
  const el = document.getElementById(elementoId);
  if (!el) return;
  el.textContent = mensagem;
  el.className = sucesso ? "text-success small mt-2" : "text-danger small mt-2";
}

async function copiarAssinaturaFormatada() {
  const previewBox = document.getElementById("preview-assinatura");
  if (!previewBox) return;
  const html = previewBox.innerHTML;
  try {
    if (navigator.clipboard && window.ClipboardItem) {
      await navigator.clipboard.write([
        new ClipboardItem({
          "text/html": new Blob([html], { type: "text/html" }),
          "text/plain": new Blob([previewBox.innerText], { type: "text/plain" }),
        }),
      ]);
      mostrarStatusCopia("status-copia", "Assinatura copiada! Cole diretamente no Novo Outlook.");
    } else {
      throw new Error("Clipboard API indisponível");
    }
  } catch (err) {
    // Fallback: seleciona o conteúdo para cópia manual (Ctrl+C)
    const range = document.createRange();
    range.selectNode(previewBox);
    window.getSelection().removeAllRanges();
    window.getSelection().addRange(range);
    try {
      document.execCommand("copy");
      mostrarStatusCopia("status-copia", "Assinatura copiada (modo compatibilidade).");
    } catch (e) {
      mostrarStatusCopia("status-copia", "Não foi possível copiar automaticamente. Selecione o texto acima e use Ctrl+C.", false);
    }
    window.getSelection().removeAllRanges();
  }
}

async function copiarHtmlPuro() {
  const previewBox = document.getElementById("preview-assinatura");
  if (!previewBox) return;
  try {
    await navigator.clipboard.writeText(previewBox.innerHTML);
    mostrarStatusCopia("status-copia", "Código HTML copiado para a área de transferência.");
  } catch (err) {
    mostrarStatusCopia("status-copia", "Não foi possível copiar o HTML automaticamente.", false);
  }
}

function testarImagem(inputId, resultadoId) {
  const input = document.getElementById(inputId);
  const resultado = document.getElementById(resultadoId);
  if (!input || !resultado) return;
  resultado.textContent = "Testando...";
  resultado.className = "small text-muted";
  fetch("/configuracoes/testar-imagem", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ url: input.value.trim() }),
  })
    .then((resp) => resp.json())
    .then((data) => {
      resultado.textContent = (data.acessivel ? "✓ " : "✕ ") + data.mensagem;
      resultado.className = data.acessivel ? "small text-success" : "small text-danger";
    })
    .catch(() => {
      resultado.textContent = "Não foi possível testar a imagem.";
      resultado.className = "small text-danger";
    });
}

document.addEventListener("DOMContentLoaded", ligarAtualizacaoAutomatica);
