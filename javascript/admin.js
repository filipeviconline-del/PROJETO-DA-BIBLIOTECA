/* ===== Painel administrativo de ativações – ToschiBook ===== */

const refreshButton = document.getElementById("refreshButton");

// Banner de status da licença
const licenseBanner = document.getElementById("licenseBanner");
const bannerTitulo = document.getElementById("bannerTitulo");
const bannerSubtitulo = document.getElementById("bannerSubtitulo");
const bannerDiasBox = document.getElementById("bannerDiasBox");
const bannerDias = document.getElementById("bannerDias");
const progressWrap = document.getElementById("licenseProgressWrap");
const progressBar = document.getElementById("licenseProgressBar");
const progressLegend = document.getElementById("licenseProgressLegend");
const legendInicio = document.getElementById("legendInicio");
const legendFim = document.getElementById("legendFim");

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

function formatarData(valor) {
    if (!valor) return "—";
    const d = new Date(valor);
    if (isNaN(d)) return valor;
    return d.toLocaleDateString("pt-BR", {
        day: "2-digit", month: "2-digit", year: "numeric",
    });
}

function definirEstadoBanner(estado) {
    licenseBanner.classList.remove("ativo", "aviso", "inativo");
    licenseBanner.classList.add(estado);
}

function renderizarBanner(licenca) {
    // Produto NÃO ativado / expirado / outra máquina
    if (!licenca || !licenca.ativado) {
        definirEstadoBanner("inativo");
        const motivo = licenca && licenca.motivo;
        if (motivo === "expirada") {
            bannerTitulo.textContent = "Licença expirada";
            bannerSubtitulo.textContent =
                "Informe um novo serial para voltar a usar o sistema.";
        } else if (motivo === "maquina_diferente") {
            bannerTitulo.textContent = "Licença de outra máquina";
            bannerSubtitulo.textContent =
                "Esta licença foi ativada em outro computador.";
        } else if (motivo === "adulterada") {
            bannerTitulo.textContent = "Licença adulterada";
            bannerSubtitulo.textContent =
                "Os dados de licença foram modificados. Reative o produto.";
        } else if (motivo === "relogio_alterado") {
            bannerTitulo.textContent = "Relógio do sistema alterado";
            bannerSubtitulo.textContent =
                "Detectamos retrocesso na data/hora. Ajuste o relógio e reative.";
        } else {
            bannerTitulo.textContent = "Produto não ativado";
            bannerSubtitulo.textContent = "Nenhuma licença ativa nesta máquina.";
        }
        bannerDiasBox.hidden = true;
        progressWrap.hidden = true;
        progressLegend.hidden = true;
        return;
    }

    // Produto ativado
    const tipo = licenca.tipo || "—";

    // Licença perpétua (sem expiração)
    if (!licenca.expira_em) {
        definirEstadoBanner("ativo");
        bannerTitulo.textContent = "Produto ativado";
        bannerSubtitulo.textContent =
            `Licença ${tipo} • sem data de expiração (perpétua).`;
        bannerDiasBox.hidden = true;
        progressWrap.hidden = true;
        progressLegend.hidden = true;
        return;
    }

    // Licença com validade -> mostra dias restantes e barra de progresso
    const dias = licenca.dias_restantes ?? 0;
    const aviso = dias <= 15;  // destaca quando falta pouco
    definirEstadoBanner(aviso ? "aviso" : "ativo");

    bannerTitulo.textContent = aviso
        ? "Licença ativa — expira em breve"
        : "Produto ativado";
    bannerSubtitulo.textContent =
        `Licença ${tipo} • válida até ${formatarData(licenca.expira_em)}.`;

    bannerDias.textContent = Math.max(dias, 0);
    bannerDiasBox.hidden = false;

    // Barra: quanto do período total já passou.
    progressWrap.hidden = false;
    progressLegend.hidden = false;

    const fim = new Date(licenca.expira_em + "T00:00:00");
    const inicio = licenca.ativado_em ? new Date(licenca.ativado_em) : null;
    let pct = 0;
    if (inicio && !isNaN(inicio) && !isNaN(fim) && fim > inicio) {
        const total = fim - inicio;
        const decorrido = Date.now() - inicio;
        pct = Math.min(Math.max((decorrido / total) * 100, 0), 100);
    } else {
        // Sem data de início: estima pelo tipo não é possível -> barra cheia parcial.
        pct = dias <= 0 ? 100 : 0;
    }
    progressBar.style.width = pct.toFixed(1) + "%";
    legendInicio.textContent = inicio ? formatarData(licenca.ativado_em) : "Início";
    legendFim.textContent = formatarData(licenca.expira_em);
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
        renderizarBanner(dados.licenca);
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
