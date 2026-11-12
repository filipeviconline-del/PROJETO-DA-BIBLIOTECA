/* ===== Dashboard ToschiBook ===== */

const refreshButton = document.getElementById("refreshButton");

const statLivros = document.getElementById("statLivros");
const statUsuarios = document.getElementById("statUsuarios");
const statEmprestimos = document.getElementById("statEmprestimos");

const emprestimosCount = document.getElementById("emprestimosCount");
const emprestimosEmpty = document.getElementById("emprestimosEmpty");
const emprestimosTable = document.getElementById("emprestimosTable");
const emprestimosBody = document.getElementById("emprestimosBody");

const livrosCount = document.getElementById("livrosCount");
const livrosEmpty = document.getElementById("livrosEmpty");
const livrosList = document.getElementById("livrosList");

const todayDate = document.getElementById("todayDate");

const MESES = [
    "janeiro", "fevereiro", "março", "abril", "maio", "junho",
    "julho", "agosto", "setembro", "outubro", "novembro", "dezembro"
];

const DIAS_SEMANA = [
    "domingo", "segunda-feira", "terça-feira", "quarta-feira",
    "quinta-feira", "sexta-feira", "sábado"
];

function formatarDataAtual() {
    const agora = new Date();
    const diaSemana = DIAS_SEMANA[agora.getDay()];
    const dia = agora.getDate();
    const mes = MESES[agora.getMonth()];
    const ano = agora.getFullYear();

    return `Hoje, ${diaSemana}, ${dia} de ${mes} de ${ano}`;
}

function formatarDataEmprestimo(valor) {
    const data = new Date(valor + "T00:00:00");
    return data.toLocaleDateString("pt-BR", {
        day: "2-digit",
        month: "2-digit",
        year: "numeric"
    });
}

function formatarSiglaLivro(titulo) {
    const palavras = titulo.trim().split(/\s+/).filter(Boolean);
    const parte = palavras.slice(0, 2).map((palavra) => palavra[0].toUpperCase());

    return parte.join("") || '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="icon-svg"><path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/></svg>';
}

async function buscar(url, opcoes) {
    const resposta = await fetch(apiUrl(url), opcoes);

    if (!resposta.ok) {
        throw new Error(`Erro ao acessar ${url} (${resposta.status})`);
    }

    return resposta.json();
}

function mostrarErro(containerId, mensagem) {
    const container = document.getElementById(containerId);
    container.hidden = false;
    container.innerHTML = "";

    const aviso = document.createElement("div");
    aviso.className = "load-error";
    aviso.textContent = mensagem;
    container.appendChild(aviso);
}

function restaurarEmptyState(containerId) {
    const container = document.getElementById(containerId);
    container.hidden = false;
    container.innerHTML = "";

    const icone = document.createElement("span");
    icone.className = "empty-icon";

    const texto = document.createElement("p");

    if (containerId === "emprestimosEmpty") {
        icone.innerHTML = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="icon-svg"><polyline points="22 12 16 12 14 15 10 15 8 12 2 12"/><path d="M5.45 5.11L2 12v6a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2v-6l-3.45-6.89A2 2 0 0 0 16.76 4H7.24a2 2 0 0 0-1.79 1.11z"/></svg>';
        texto.textContent = "Nenhum empréstimo ativo no momento.";
    } else {
        icone.innerHTML = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="icon-svg"><path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/></svg>';
        texto.textContent = "Nenhum livro cadastrado ainda.";
    }

    container.append(icone, texto);
}

function renderizarEstatisticas(dados) {
    statLivros.textContent = dados.total_livros ?? 0;
    statUsuarios.textContent = dados.total_usuarios ?? 0;
    statEmprestimos.textContent = dados.emprestimos_ativos ?? 0;
}

function renderizarEmprestimos(emprestimos) {
    emprestimosCount.textContent = emprestimos.length;

    const temEmprestimos = emprestimos.length > 0;

    emprestimosTable.hidden = !temEmprestimos;
    emprestimosEmpty.hidden = temEmprestimos;

    if (!temEmprestimos) {
        restaurarEmptyState("emprestimosEmpty");
    }

    emprestimosBody.innerHTML = "";

    emprestimos.forEach((emprestimo) => {
        const linha = document.createElement("tr");

        const celulaLivro = document.createElement("td");
        celulaLivro.className = "book-title-cell";
        celulaLivro.textContent = emprestimo.titulo || "—";

        const celulaAluno = document.createElement("td");
        celulaAluno.textContent = emprestimo.usuario_nome || "—";

        const celulaTurma = document.createElement("td");
        celulaTurma.className = "small-text";
        celulaTurma.textContent = emprestimo.turma || "—";

        const celulaData = document.createElement("td");
        celulaData.className = "small-text";
        celulaData.textContent = formatarDataEmprestimo(emprestimo.data_emprestimo);

        const celulaAcoes = document.createElement("td");
        celulaAcoes.className = "table-actions";

        const btnDevolver = document.createElement("button");
        btnDevolver.type = "button";
        btnDevolver.className = "btn btn-return btn-small";
        btnDevolver.innerHTML = "⎌ Devolver";
        btnDevolver.addEventListener("click", () => devolverLivro(emprestimo));

        celulaAcoes.appendChild(btnDevolver);

        linha.append(celulaLivro, celulaAluno, celulaTurma, celulaData, celulaAcoes);
        emprestimosBody.appendChild(linha);
    });
}

function renderizarLivros(livros) {
    const recentes = livros.slice(0, 5);

    livrosCount.textContent = livros.length;

    const listaVazia = recentes.length === 0;
    livrosEmpty.hidden = !listaVazia;

    if (listaVazia) {
        restaurarEmptyState("livrosEmpty");
    }

    livrosList.innerHTML = "";

    recentes.forEach((livro) => {
        const item = document.createElement("li");

        const capa = document.createElement("span");
        capa.className = "book-cover";
        capa.textContent = formatarSiglaLivro(livro.titulo);

        const meta = document.createElement("span");
        meta.className = "book-meta";

        const titulo = document.createElement("strong");
        titulo.textContent = livro.titulo;

        const autor = document.createElement("small");
        autor.textContent = livro.autor || "Autor desconhecido";

        meta.append(titulo, autor);

        const copias = document.createElement("span");
        copias.className = "book-copies";

        const quantidade = livro.quantidade ?? 1;
        copias.textContent = quantidade === 1
            ? "1 exemplar"
            : `${quantidade} exemplares`;

        item.append(capa, meta, copias);
        livrosList.appendChild(item);
    });
}

async function devolverLivro(emprestimo) {
    const confirmacao = confirm(
        `Registrar a devolução de "${emprestimo.titulo}" para ${emprestimo.usuario_nome}?`
    );

    if (!confirmacao) {
        return;
    }

    try {
        await buscar(`/api/emprestimos/${emprestimo.id}/devolver`, {
            method: "POST"
        });
        await atualizarDashboard();
    } catch (erro) {
        alert(erro.message || "Erro ao registrar devolução");
    }
}

async function atualizarDashboard() {
    refreshButton.disabled = true;

    try {
        const [estatisticas, emprestimos, livros] = await Promise.all([
            buscar("/api/estatisticas"),
            buscar("/api/emprestimos"),
            buscar("/api/livros")
        ]);

        renderizarEstatisticas(estatisticas);
        renderizarEmprestimos(emprestimos);
        renderizarLivros(livros);
    } catch (erro) {
        const mensagem = "Não foi possível carregar os dados. Verifique se o servidor está rodando.";
        mostrarErro("emprestimosEmpty", mensagem);
        mostrarErro("livrosEmpty", mensagem);
    } finally {
        refreshButton.disabled = false;
    }
}

// ===== Status resumido da licença (chip no topo) =====
async function carregarStatusLicenca() {
    const chip = document.getElementById("licenseChip");
    const chipIcon = document.getElementById("chipIcon");
    const chipText = document.getElementById("chipText");
    const chipDias = document.getElementById("chipDias");
    if (!chip) return;

    try {
        const resp = await fetch(apiUrl("/api/licenca/status"));
        const lic = await resp.json();
        chip.hidden = false;
        chip.classList.remove("ativo", "aviso", "inativo");

        if (!lic.ativado) {
            chip.classList.add("inativo");
            chipText.textContent = lic.motivo === "expirada"
                ? "Licença expirada"
                : "Produto não ativado";
            chipDias.hidden = true;
            return;
        }

        if (!lic.expira_em) {
            chip.classList.add("ativo");
            chipText.textContent = `Produto ativado • licença ${lic.tipo} (perpétua)`;
            chipDias.hidden = true;
            return;
        }

        const dias = lic.dias_restantes ?? 0;
        const aviso = dias <= 15;
        chip.classList.add(aviso ? "aviso" : "ativo");
        chipText.textContent =
            `Produto ativado • licença ${lic.tipo} • válida até ${lic.expira_em}`;
        chipDias.hidden = false;
        chipDias.textContent = `${Math.max(dias, 0)} dias restantes`;
    } catch {
        chip.hidden = true;
    }
}

todayDate.textContent = formatarDataAtual();

refreshButton.addEventListener("click", atualizarDashboard);

atualizarDashboard();
carregarStatusLicenca();
