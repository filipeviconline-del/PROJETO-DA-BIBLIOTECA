/* Recuperação de senha por pergunta de segurança — ToschiBook */

const stepIdentify = document.getElementById("stepIdentify");
const stepReset = document.getElementById("stepReset");
const identInput = document.getElementById("identificador");
const identError = document.getElementById("identError");
const perguntaTexto = document.getElementById("perguntaTexto");
const respostaInput = document.getElementById("resposta");
const respostaError = document.getElementById("respostaError");
const novaSenhaInput = document.getElementById("novaSenha");
const senhaError = document.getElementById("senhaError");
const statusMessage = document.getElementById("statusMessage");
const btnBuscar = document.getElementById("btnBuscar");
const btnRedefinir = document.getElementById("btnRedefinir");
const togglePw = document.getElementById("togglePw");

let identificadorAtual = "";

function status(texto, tipo) {
    statusMessage.textContent = texto;
    statusMessage.className = "status-message" + (tipo ? " " + tipo : "");
}

function carregando(botao, ativo) {
    botao.classList.toggle("loading", ativo);
    botao.disabled = ativo;
}

togglePw.addEventListener("click", () => {
    const ocultando = novaSenhaInput.type === "password";
    novaSenhaInput.type = ocultando ? "text" : "password";
    togglePw.textContent = ocultando ? "Ocultar" : "Mostrar";
});

/* Etapa 1: busca a pergunta de segurança da conta. */
stepIdentify.addEventListener("submit", async (e) => {
    e.preventDefault();
    identError.textContent = "";
    status("", "");

    const identificador = identInput.value.trim();
    if (!identificador) {
        identError.textContent = "Informe seu e-mail ou usuário.";
        return;
    }

    carregando(btnBuscar, true);
    try {
        const resp = await fetch(apiUrl("/api/auth/recuperar/pergunta"), {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ identificador }),
        });
        const dados = await resp.json();

        if (!resp.ok) {
            status(dados.erro || "Não foi possível continuar.", "error");
            return;
        }

        identificadorAtual = identificador;
        perguntaTexto.textContent = dados.pergunta;
        stepIdentify.hidden = true;
        stepReset.hidden = false;
        respostaInput.focus();
    } catch {
        status("Erro de conexão com o servidor.", "error");
    } finally {
        carregando(btnBuscar, false);
    }
});

/* Etapa 2: valida a resposta e redefine a senha. */
stepReset.addEventListener("submit", async (e) => {
    e.preventDefault();
    respostaError.textContent = "";
    senhaError.textContent = "";
    status("", "");

    const resposta = respostaInput.value.trim();
    const nova_senha = novaSenhaInput.value;
    let ok = true;
    if (!resposta) {
        respostaError.textContent = "Informe sua resposta.";
        ok = false;
    }
    if (nova_senha.length < 6) {
        senhaError.textContent = "A nova senha deve ter pelo menos 6 caracteres.";
        ok = false;
    }
    if (!ok) return;

    carregando(btnRedefinir, true);
    try {
        const resp = await fetch(apiUrl("/api/auth/recuperar/redefinir"), {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                identificador: identificadorAtual, resposta, nova_senha,
            }),
        });
        const dados = await resp.json();

        if (!resp.ok) {
            status(dados.erro || "Não foi possível redefinir.", "error");
            return;
        }

        status("✓ " + (dados.mensagem || "Senha redefinida!") + " Redirecionando...",
               "success");
        setTimeout(() => (window.location.href = "index.html"), 2000);
    } catch {
        status("Erro de conexão com o servidor.", "error");
    } finally {
        carregando(btnRedefinir, false);
    }
});

[identInput, respostaInput, novaSenhaInput].forEach((i) =>
    i.addEventListener("input", () => status("", "")));
