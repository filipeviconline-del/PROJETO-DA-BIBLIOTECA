/* ===== Painel administrativo de ativações – ToschiBook ===== */

const refreshButton = document.getElementById("refreshButton");

const statTipo = document.getElementById("statTipo");
const statAtivacoes = document.getElementById("statAtivacoes");
const statValidade = document.getElementById("statValidade");
const statMaquina = document.getElementById("statMaquina");

const seriaisCount = document.getElementById("seriaisCount");
const seriaisEmpty = document.getElementById("seriaisEmpty");
const seriaisTable = document.getElementById("seriaisTable");
const seriaisBody = document.getElementById("seriaisBody");

const ativacoesCount = document.getElementById("ativacoesCount");
const ativacoesEmpty = document.getElementById("ativacoesEmpty");
const ativacoesTable = document.getElementById("ativacoesTable");
const ativacoesBody = document.getElementById("ativacoesBody");

function formatarDataHora(valor) {
    if (!valor) return "—";
    const data = new Date(valor);
    if (isNaN(data)) return valor;
    return data.toLocaleString("pt-BR", {
        day: "2-digit",
        month: "2-digit",
        year: "numeric",
        hour: "2-digit",
        minute: "2-digit",
    });
}

function rotuloLimite(limite) {
    if (limite === 0) return "ilimitado";
    if (limite == null) return "—";
    return String(limite);
}

async function buscar(url, opcoes) {
    const resposta = await fetch(apiUrl(url), opcoes);
    if (resposta.status === 401) {
        // Sessão ausente/expirada -> volta ao login.
        window.location.href = "/html/index.html";
        throw new Error("Não autenticado");
    }
    if (!resposta.ok) {
        throw new Error(`Erro ao acessar ${url} (${resposta.status})`);
    }
    return resposta.json();
}

function renderizarResumoLicenca(licenca, idMaquina) {
    statMaquina.textContent = idMaquina || "—";

    if (!licenca || !licenca.ativado) {
        statTipo.textContent = "Não ativada";
        statAtivacoes.textContent = "—";
        statValidade.textContent = "—";
        return;
    }

    statTipo.textContent = licenca.tipo || "—";

    const max = licenca.max_ativacoes;
    const usadas = licenca.ativacoes_usadas ?? 0;
    statAtivacoes.textContent = max === 0
        ? `${usadas} / ∞`
        : `${usadas} / ${max ?? "—"}`;

    if (licenca.expira_em) {
        const dias = licenca.dias_restantes;
        const sufixo = (dias != null) ? ` (${dias} dias)` : "";
        statValidade.textContent = `até ${licenca.expira_em}${sufixo}`;
    } else {
        statValidade.textContent = "Perpétua";
    }
}

function renderizarSeriais(lista) {
    seriaisCount.textContent = lista.length;
    const vazio = lista.length === 0;
    seriaisTable.hidden = vazio;
    seriaisEmpty.hidden = !vazio;

    seriaisBody.innerHTML = "";

    lista.forEach((item) => {
        const tr = document.createElement("tr");

        const tdSerial = document.createElement("td");
        tdSerial.className = "mono-cell";
        tdSerial.textContent = item.serial;

        const tdTipo = document.createElement("td");
        tdTipo.textContent = item.tipo || "—";

        const tdMaquinas = document.createElement("td");
        const cheio = item.max_ativacoes && item.maquinas >= item.max_ativacoes;
        tdMaquinas.className = cheio ? "uso-cheio" : "uso-ok";
        tdMaquinas.textContent = item.maquinas;

        const tdLimite = document.createElement("td");
        tdLimite.className = "small-text";
        tdLimite.textContent = rotuloLimite(item.max_ativacoes);

        const tdUltima = document.createElement("td");
        tdUltima.className = "small-text";
        tdUltima.textContent = formatarDataHora(item.ultima_ativacao);

        tr.append(tdSerial, tdTipo, tdMaquinas, tdLimite, tdUltima);
        seriaisBody.appendChild(tr);
    });
}

function renderizarAtivacoes(lista) {
    ativacoesCount.textContent = lista.length;
    const vazio = lista.length === 0;
    ativacoesTable.hidden = vazio;
    ativacoesEmpty.hidden = !vazio;

    ativacoesBody.innerHTML = "";

    lista.forEach((item) => {
        const tr = document.createElement("tr");

        const tdSerial = document.createElement("td");
        tdSerial.className = "mono-cell";
        tdSerial.textContent = item.serial;

        const tdMaquina = document.createElement("td");
        tdMaquina.className = "mono-cell";
        tdMaquina.textContent = item.id_maquina;
        if (item.maquina_atual) {
            const tag = document.createElement("span");
            tag.className = "tag-atual";
            tag.textContent = "esta máquina";
            tdMaquina.appendChild(tag);
        }

        const tdData = document.createElement("td");
        tdData.className = "small-text";
        tdData.textContent = formatarDataHora(item.ativado_em);

        const tdAcoes = document.createElement("td");
        tdAcoes.className = "table-actions";
        const btn = document.createElement("button");
        btn.type = "button";
        btn.className = "btn btn-danger btn-small";
        btn.textContent = "Revogar";
        btn.addEventListener("click", () => revogar(item));
        tdAcoes.appendChild(btn);

        tr.append(tdSerial, tdMaquina, tdData, tdAcoes);
        ativacoesBody.appendChild(tr);
    });
}

async function revogar(item) {
    let aviso = `Revogar a ativação da máquina ${item.id_maquina}?\n\nIsso libera uma vaga para o serial ${item.serial}.`;
    if (item.maquina_atual) {
        aviso += "\n\nATENÇÃO: esta é a máquina atual — o sistema será bloqueado e exigirá nova ativação.";
    }
    if (!confirm(aviso)) return;

    try {
        await buscar(`/api/licenca/ativacoes/${item.id}`, { method: "DELETE" });
        if (item.maquina_atual) {
            // A licença local foi removida -> vai para a tela de ativação.
            window.location.href = "/html/ativacao.html";
            return;
        }
        await carregar();
    } catch (erro) {
        alert(erro.message || "Erro ao revogar ativação.");
    }
}

async function carregar() {
    refreshButton.disabled = true;
    try {
        const dados = await buscar("/api/licenca/ativacoes");
        renderizarResumoLicenca(dados.licenca, dados.id_maquina);
        renderizarSeriais(dados.resumo_seriais || []);
        renderizarAtivacoes(dados.ativacoes || []);
    } catch (erro) {
        if (erro.message === "Não autenticado") return;
        seriaisEmpty.hidden = false;
        seriaisEmpty.innerHTML = '<div class="load-error">Não foi possível carregar as ativações.</div>';
        ativacoesEmpty.hidden = false;
        ativacoesEmpty.innerHTML = '<div class="load-error">Não foi possível carregar as ativações.</div>';
    } finally {
        refreshButton.disabled = false;
    }
}

refreshButton.addEventListener("click", carregar);

carregar();
