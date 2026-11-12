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

/* Formata o que o usuário digita em grupos de 5: XXXXX-XXXXX-... */
function formatarSerial(valor) {
    const limpo = valor
        .toUpperCase()
        .split("")
        .filter((c) => ALFABETO.test(c))
        .join("")
        .slice(0, 25);

    return limpo.match(/.{1,5}/g)?.join("-") ?? "";
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

    if (serial.replace(/-/g, "").length !== 25) {
        serialError.textContent = "O serial deve ter 25 caracteres.";
        return;
    }

    carregando(true);
    mostrarStatus("Validando serial...", "");

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
        }
    } catch {
        mostrarStatus("Erro de conexão com o servidor.", "erro");
    } finally {
        carregando(false);
    }
});

carregarMaquina();
verificarJaAtivado();
