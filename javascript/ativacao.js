/* Lógica da tela de ativação por serial do ToschiBook */

const form = document.getElementById("activationForm");
const serialInput = document.getElementById("serial");
const serialError = document.getElementById("serialError");
const statusMessage = document.getElementById("statusMessage");
const activateButton = document.getElementById("activateButton");
const machineIdEl = document.getElementById("machineId");
const yearEl = document.getElementById("currentYear");

if (yearEl) yearEl.textContent = new Date().getFullYear();

// Alfabeto aceito no serial (sem caracteres ambíguos).
const ALFABETO = /[ABCDEFGHJKLMNPQRSTUVWXYZ23456789]/;

/* Formata o que o usuário digita em grupos de 5.
   Aceita dois formatos:
     - serial universal: XXXXX-XXXXX-XXXXX-XXXXX-XXXXX (25 caracteres)
     - código de máquina: TBM-XXXXX-... (36 caracteres após o prefixo) */
function formatarSerial(valor) {
    const bruto = valor.toUpperCase().replace(/[^A-Z0-9]/g, "");

    // Código vinculado à máquina (começa com TBM)
    if (bruto.startsWith("TBM")) {
        const corpo = bruto.slice(3)
            .split("").filter((c) => ALFABETO.test(c)).join("").slice(0, 36);
        const grupos = corpo.match(/.{1,5}/g)?.join("-") ?? "";
        return grupos ? "TBM-" + grupos : "TBM-";
    }

    // Serial universal
    const limpo = bruto.split("").filter((c) => ALFABETO.test(c)).join("").slice(0, 25);
    return limpo.match(/.{1,5}/g)?.join("-") ?? "";
}

/* Comprimento (sem hífens) esperado conforme o formato digitado. */
function tamanhoEsperado(valor) {
    return valor.toUpperCase().replace(/[^A-Z0-9]/g, "").startsWith("TBM")
        ? 39   // TBM + 36
        : 25;
}

serialInput.addEventListener("input", (e) => {
    const posFinal = e.target.selectionEnd === e.target.value.length;
    e.target.value = formatarSerial(e.target.value);
    serialError.textContent = "";
    if (posFinal) {
        e.target.setSelectionRange(e.target.value.length, e.target.value.length);
    }
});

/* Mostra o status atual da tela (mensagem). */
function mostrarStatus(texto, tipo) {
    statusMessage.textContent = texto;
    statusMessage.className = "status-message" + (tipo ? " " + tipo : "");
}

function carregando(ativo) {
    activateButton.classList.toggle("loading", ativo);
    activateButton.disabled = ativo;
}

/* Carrega o ID da máquina para exibir ao usuário. */
async function carregarMaquina() {
    try {
        const resp = await fetch(apiUrl("/api/licenca/maquina"));
        const dados = await resp.json();
        machineIdEl.textContent = dados.id_maquina || "indisponível";
    } catch {
        machineIdEl.textContent = "indisponível";
    }
}

/* Botão "Copiar ID" — facilita o cliente enviar o ID ao suporte. */
const copyMachineBtn = document.getElementById("copyMachine");
if (copyMachineBtn) {
    copyMachineBtn.addEventListener("click", async () => {
        const id = (machineIdEl.textContent || "").trim();
        if (!id || id === "indisponível" || id === "...") return;
        try {
            await navigator.clipboard.writeText(id);
            const original = copyMachineBtn.textContent;
            copyMachineBtn.textContent = "Copiado!";
            setTimeout(() => (copyMachineBtn.textContent = original), 1500);
        } catch {
            // Fallback: seleciona o texto para o usuário copiar manualmente.
            const faixa = document.createRange();
            faixa.selectNodeContents(machineIdEl);
            const sel = window.getSelection();
            sel.removeAllRanges();
            sel.addRange(faixa);
        }
    });
}

/* Se já estiver ativado, não faz sentido ficar nesta tela. */
async function verificarJaAtivado() {
    try {
        const resp = await fetch(apiUrl("/api/licenca/status"));
        const dados = await resp.json();
        if (dados.ativado) {
            mostrarStatus("Produto já ativado. Redirecionando...", "sucesso");
            setTimeout(() => (window.location.href = "index.html"), 1200);
        }
    } catch {
        /* silencioso */
    }
}

form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const serial = serialInput.value.trim();

    const semHifen = serial.replace(/-/g, "").length;
    if (semHifen !== tamanhoEsperado(serial)) {
        serialError.textContent = serial.toUpperCase().startsWith("TBM")
            ? "Código de ativação incompleto."
            : "O serial deve ter 25 caracteres.";
        return;
    }

    carregando(true);
    mostrarStatus("Validando...", "");

    try {
        const resp = await fetch(apiUrl("/api/licenca/ativar"), {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ serial }),
        });
        const dados = await resp.json();

        if (resp.ok && dados.sucesso) {
            let validade;
            if (dados.expira_em) {
                const fim = new Date(dados.expira_em + "T00:00:00");
                const diasRest = Math.max(
                    Math.ceil((fim - Date.now()) / 86400000), 0);
                validade = ` Válida até ${dados.expira_em} (${diasRest} dias restantes).`;
            } else {
                validade = " Licença perpétua (sem expiração).";
            }
            let ativacoes = "";
            if (dados.max_ativacoes && dados.max_ativacoes > 0) {
                ativacoes = ` Ativações: ${dados.ativacoes_usadas}/${dados.max_ativacoes}.`;
            } else if (dados.max_ativacoes === 0) {
                ativacoes = " Ativações ilimitadas.";
            }
            mostrarStatus(
                "✓ " + (dados.mensagem || "Produto ativado!") + validade + ativacoes
                + " Redirecionando...",
                "sucesso");
            // Tempo maior para o usuário conseguir ler a confirmação.
            setTimeout(() => (window.location.href = "index.html"), 3500);
        } else {
            mostrarStatus(dados.erro || "Não foi possível ativar.", "erro");
            // Falhou: roda o diagnóstico automaticamente para explicar o motivo.
            diagnosticar(serial);
        }
    } catch {
        mostrarStatus("Erro de conexão com o servidor.", "erro");
    } finally {
        carregando(false);
    }
});

/* ===== Diagnóstico de ativação ===== */
const diagnoseButton = document.getElementById("diagnoseButton");
const diagnoseBox = document.getElementById("diagnoseBox");
const diagTitulo = document.getElementById("diagTitulo");
const diagMensagem = document.getElementById("diagMensagem");
const diagSugestao = document.getElementById("diagSugestao");
const diagExtra = document.getElementById("diagExtra");

const TITULOS_PROBLEMA = {
    vazio: "Campo vazio",
    tamanho: "Código incompleto",
    chave_ou_corrompido: "Chave diferente ou código corrompido",
    maquina_diferente: "Código de outro computador",
};

async function diagnosticar(serial) {
    try {
        const resp = await fetch(apiUrl("/api/licenca/diagnosticar"), {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ serial }),
        });
        const d = await resp.json();

        diagnoseBox.hidden = false;
        diagnoseBox.classList.toggle("ok", !!d.ok);
        diagnoseBox.classList.toggle("erro", !d.ok);

        if (d.ok) {
            diagTitulo.textContent = "✓ Tudo certo com este código";
            diagMensagem.textContent = d.mensagem || "";
            diagSugestao.textContent = d.sugestao || "Clique em 'Ativar produto'.";
        } else {
            diagTitulo.textContent =
                "✗ " + (TITULOS_PROBLEMA[d.problema] || "Não foi possível ativar");
            diagMensagem.textContent = d.mensagem || "";
            diagSugestao.textContent = d.sugestao || "";
        }
        diagExtra.textContent =
            `ID desta máquina: ${d.id_maquina || "—"}  •  Chave: ${d.impressao_chave || "—"}`;
    } catch {
        diagnoseBox.hidden = false;
        diagnoseBox.classList.add("erro");
        diagTitulo.textContent = "Não foi possível diagnosticar";
        diagMensagem.textContent = "Erro de conexão com o servidor.";
        diagSugestao.textContent = "";
        diagExtra.textContent = "";
    }
}

if (diagnoseButton) {
    diagnoseButton.addEventListener("click", () => {
        diagnosticar(serialInput.value.trim());
    });
}

carregarMaquina();
verificarJaAtivado();
