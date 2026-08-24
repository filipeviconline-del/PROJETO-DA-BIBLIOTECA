/* ===== Página de Empréstimos - ToschiBook ===== */

const btnNovoEmprestimo = document.getElementById("btnNovoEmprestimo");
const buscaEmprestimo = document.getElementById("buscaEmprestimo");
const emprestimosCount = document.getElementById("emprestimosCount");
const emprestimosEmpty = document.getElementById("emprestimosEmpty");
const emprestimosTable = document.getElementById("emprestimosTable");
const emprestimosBody = document.getElementById("emprestimosBody");

const modalEmprestimo = document.getElementById("modalEmprestimo");
const modalTitulo = document.getElementById("modalTitulo");
const fecharModal = document.getElementById("fecharModal");
const cancelarModal = document.getElementById("cancelarModal");
const formEmprestimo = document.getElementById("formEmprestimo");
const livroSelect = document.getElementById("livroSelect");
const livroHint = document.getElementById("livroHint");
const usuarioSelect = document.getElementById("usuarioSelect");
const salvarEmprestimo = document.getElementById("salvarEmprestimo");

let emprestimos = [];
let livros = [];
let usuarios = [];
let termoBusca = "";

async function buscar(url, opcoes) {
    const resposta = await fetch(apiUrl(url), opcoes);

    if (!resposta.ok) {
        const erro = await resposta.json().catch(() => ({}));
        throw new Error(erro.erro || `Erro ${resposta.status}`);
    }

    return resposta.json();
}

function formatarData(valor) {
    if (!valor) {
        return "—";
    }

    // A API retorna datas no formato "YYYY-MM-DD HH:MM:SS" ou "YYYY-MM-DD"
    const data = new Date(valor.includes("T") ? valor : valor.replace(" ", "T"));

    if (Number.isNaN(data.getTime())) {
        return "—";
    }

    return data.toLocaleDateString("pt-BR", {
        day: "2-digit",
        month: "2-digit",
        year: "numeric"
    });
}

function mostrarErro(mensagem) {
    emprestimosTable.hidden = true;

    emprestimosEmpty.hidden = false;
    emprestimosEmpty.innerHTML = "";

    const aviso = document.createElement("div");
    aviso.className = "load-error";
    aviso.textContent = mensagem;
    emprestimosEmpty.appendChild(aviso);
}

function renderizarEmprestimos() {
    const filtrados = emprestimos.filter((emprestimo) => {
        if (!termoBusca) {
            return true;
        }

        const termo = termoBusca.toLowerCase();
        return (
            emprestimo.titulo.toLowerCase().includes(termo) ||
            emprestimo.usuario_nome.toLowerCase().includes(termo)
        );
    });

    emprestimosCount.textContent = `${filtrados.length} registro(s)`;

    const temEmprestimos = filtrados.length > 0;
    emprestimosTable.hidden = !temEmprestimos;
    emprestimosEmpty.hidden = temEmprestimos;

    if (!temEmprestimos) {
        emprestimosEmpty.innerHTML = "";
        const icone = document.createElement("span");
        icone.className = "empty-icon";
        icone.innerHTML = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="icon-svg"><polyline points="22 12 16 12 14 15 10 15 8 12 2 12"/><path d="M5.45 5.11L2 12v6a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2v-6l-3.45-6.89A2 2 0 0 0 16.76 4H7.24a2 2 0 0 0-1.79 1.11z"/></svg>';

        const texto = document.createElement("p");
        texto.textContent = termoBusca
            ? "Nenhum empréstimo encontrado para esta busca."
            : "Nenhum empréstimo ativo no momento.";

        emprestimosEmpty.append(icone, texto);
        return;
    }

    emprestimosBody.innerHTML = "";

    filtrados.forEach((emprestimo) => {
        const linha = document.createElement("tr");

        const celulaLivro = document.createElement("td");
        celulaLivro.className = "book-title-cell";
        celulaLivro.textContent = emprestimo.titulo;

        const celulaAluno = document.createElement("td");
        celulaAluno.textContent = emprestimo.usuario_nome;

        const celulaTurma = document.createElement("td");
        celulaTurma.className = "small-text";
        celulaTurma.textContent = emprestimo.turma || "—";

        const celulaData = document.createElement("td");
        celulaData.className = "small-text";
        celulaData.textContent = formatarData(emprestimo.data_emprestimo);

        const celulaStatus = document.createElement("td");
        const badge = document.createElement("span");
        badge.className = "badge-status ativo";
        badge.textContent = "Ativo";
        celulaStatus.appendChild(badge);

        const celulaAcoes = document.createElement("td");
        celulaAcoes.className = "table-actions";

        const btnDevolver = document.createElement("button");
        btnDevolver.type = "button";
        btnDevolver.className = "btn btn-return btn-small";
        btnDevolver.innerHTML = "⎌ Devolver";
        btnDevolver.addEventListener("click", () => devolverLivro(emprestimo));

        celulaAcoes.appendChild(btnDevolver);
        linha.append(celulaLivro, celulaAluno, celulaTurma, celulaData, celulaStatus, celulaAcoes);
        emprestimosBody.appendChild(linha);
    });
}

async function carregarEmprestimos() {
    try {
        emprestimos = await buscar("/api/emprestimos");
        renderizarEmprestimos();
    } catch (erro) {
        mostrarErro("Não foi possível carregar os empréstimos. Verifique se o servidor está rodando.");
    }
}

async function carregarOpcoes() {
    try {
        const [livrosResposta, usuariosResposta] = await Promise.all([
            buscar("/api/livros"),
            buscar("/api/usuarios")
        ]);

        livros = livrosResposta;
        usuarios = usuariosResposta;

        preencherSelects();
    } catch (erro) {
        alert("Não foi possível carregar livros e usuários.");
    }
}

function preencherSelects() {
    livroSelect.innerHTML = '<option value="">Selecione um livro...</option>';
    usuarioSelect.innerHTML = '<option value="">Selecione um aluno...</option>';

    livros.forEach((livro) => {
        const opcao = document.createElement("option");
        opcao.value = livro.id;
        opcao.textContent = `${livro.titulo} (${livro.autor})`;
        livroSelect.appendChild(opcao);
    });

    usuarios.forEach((usuario) => {
        const opcao = document.createElement("option");
        opcao.value = usuario.id;
        opcao.textContent = `${usuario.nome} — ${usuario.matricula}`;
        usuarioSelect.appendChild(opcao);
    });

    atualizarHintLivro();
}

function atualizarHintLivro() {
    const livro = livros.find((item) => String(item.id) === livroSelect.value);

    if (!livro) {
        livroHint.textContent = "";
        return;
    }

    const emprestados = emprestimos.filter(
        (item) => item.livro_id === livro.id
    ).length;

    const disponiveis = Math.max(livro.quantidade - emprestados, 0);
    livroHint.textContent = `${disponiveis} exemplar(es) disponível(is)`;
}

function abrirModal() {
    modalTitulo.textContent = "Novo empréstimo";
    formEmprestimo.reset();
    livroSelect.value = "";
    usuarioSelect.value = "";
    atualizarHintLivro();

    modalEmprestimo.hidden = false;
    livroSelect.focus();
}

function fecharModalEmprestimo() {
    modalEmprestimo.hidden = true;
    formEmprestimo.reset();
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
        await carregarEmprestimos();
    } catch (erro) {
        alert(erro.message);
    }
}

async function salvarEmprestimoHandler(event) {
    event.preventDefault();

    const livroId = livroSelect.value;
    const usuarioId = usuarioSelect.value;

    if (!livroId || !usuarioId) {
        alert("Selecione um livro e um aluno.");
        return;
    }

    salvarEmprestimo.disabled = true;

    try {
        await buscar("/api/emprestimos", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                livro_id: Number(livroId),
                usuario_id: Number(usuarioId)
            })
        });

        fecharModalEmprestimo();
        await carregarEmprestimos();
    } catch (erro) {
        alert(erro.message);
    } finally {
        salvarEmprestimo.disabled = false;
    }
}

btnNovoEmprestimo.addEventListener("click", abrirModal);
fecharModal.addEventListener("click", fecharModalEmprestimo);
cancelarModal.addEventListener("click", fecharModalEmprestimo);

modalEmprestimo.addEventListener("click", (event) => {
    if (event.target === modalEmprestimo) {
        fecharModalEmprestimo();
    }
});

formEmprestimo.addEventListener("submit", salvarEmprestimoHandler);
livroSelect.addEventListener("change", atualizarHintLivro);

buscaEmprestimo.addEventListener("input", (event) => {
    termoBusca = event.target.value.trim();
    renderizarEmprestimos();
});

carregarEmprestimos();
carregarOpcoes();
