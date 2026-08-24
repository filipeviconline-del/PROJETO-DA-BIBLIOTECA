/* ===== Página de Usuários - ToschiBook ===== */

const btnNovoUsuario = document.getElementById("btnNovoUsuario");
const buscaUsuario = document.getElementById("buscaUsuario");
const usuariosCount = document.getElementById("usuariosCount");
const usuariosEmpty = document.getElementById("usuariosEmpty");
const usuariosTable = document.getElementById("usuariosTable");
const usuariosBody = document.getElementById("usuariosBody");

const modalUsuario = document.getElementById("modalUsuario");
const modalTitulo = document.getElementById("modalTitulo");
const fecharModal = document.getElementById("fecharModal");
const cancelarModal = document.getElementById("cancelarModal");
const formUsuario = document.getElementById("formUsuario");
const usuarioIdInput = document.getElementById("usuarioId");
const nomeInput = document.getElementById("nome");
const emailInput = document.getElementById("email");
const matriculaInput = document.getElementById("matricula");
const turmaInput = document.getElementById("turma");
const salvarUsuario = document.getElementById("salvarUsuario");

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

function abrirModal(usuario = null) {
    modalTitulo.textContent = usuario ? "Editar usuário" : "Novo usuário";
    usuarioIdInput.value = usuario ? usuario.id : "";

    nomeInput.value = usuario ? usuario.nome : "";
    emailInput.value = usuario ? usuario.email : "";
    matriculaInput.value = usuario ? usuario.matricula : "";
    turmaInput.value = usuario ? usuario.turma ?? "" : "";

    modalUsuario.hidden = false;
    nomeInput.focus();
}

function fecharModalUsuario() {
    modalUsuario.hidden = true;
    formUsuario.reset();
}

function mostrarErro(mensagem) {
    usuariosTable.hidden = true;

    usuariosEmpty.hidden = false;
    usuariosEmpty.innerHTML = "";

    const aviso = document.createElement("div");
    aviso.className = "load-error";
    aviso.textContent = mensagem;
    usuariosEmpty.appendChild(aviso);
}

function renderizarUsuarios() {
    const filtrados = usuarios.filter((usuario) => {
        if (!termoBusca) {
            return true;
        }

        const termo = termoBusca.toLowerCase();
        return (
            usuario.nome.toLowerCase().includes(termo) ||
            usuario.matricula.toLowerCase().includes(termo)
        );
    });

    usuariosCount.textContent = `${filtrados.length} registro(s)`;

    const temUsuarios = filtrados.length > 0;
    usuariosTable.hidden = !temUsuarios;
    usuariosEmpty.hidden = temUsuarios;

    if (!temUsuarios) {
        usuariosEmpty.innerHTML = "";
        const icone = document.createElement("span");
        icone.className = "empty-icon";
        icone.innerHTML = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="icon-svg"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>';

        const texto = document.createElement("p");
        texto.textContent = termoBusca
            ? "Nenhum usuário encontrado para esta busca."
            : "Nenhum usuário cadastrado ainda.";

        usuariosEmpty.append(icone, texto);
        return;
    }

    usuariosBody.innerHTML = "";

    filtrados.forEach((usuario) => {
        const linha = document.createElement("tr");

        const celulaNome = document.createElement("td");
        celulaNome.className = "book-title-cell";
        celulaNome.textContent = usuario.nome;

        const celulaEmail = document.createElement("td");
        celulaEmail.className = "small-text";
        celulaEmail.textContent = usuario.email;

        const celulaMatricula = document.createElement("td");
        celulaMatricula.textContent = usuario.matricula;

        const celulaTurma = document.createElement("td");
        celulaTurma.className = "small-text";
        celulaTurma.textContent = usuario.turma || "—";

        const celulaAcoes = document.createElement("td");
        celulaAcoes.className = "table-actions";

        const btnEditar = document.createElement("button");
        btnEditar.type = "button";
        btnEditar.className = "btn btn-secondary btn-small";
        btnEditar.textContent = "Editar";
        btnEditar.addEventListener("click", () => abrirModal(usuario));

        const btnExcluir = document.createElement("button");
        btnExcluir.type = "button";
        btnExcluir.className = "btn btn-danger btn-small";
        btnExcluir.textContent = "Excluir";
        btnExcluir.addEventListener("click", () => excluirUsuario(usuario));

        celulaAcoes.append(btnEditar, btnExcluir);
        linha.append(celulaNome, celulaEmail, celulaMatricula, celulaTurma, celulaAcoes);
        usuariosBody.appendChild(linha);
    });
}

async function carregarUsuarios() {
    try {
        usuarios = await buscar("/api/usuarios");
        renderizarUsuarios();
    } catch (erro) {
        mostrarErro("Não foi possível carregar os usuários. Verifique se o servidor está rodando.");
    }
}

async function excluirUsuario(usuario) {
    const confirmacao = confirm(`Excluir o usuário "${usuario.nome}"?`);

    if (!confirmacao) {
        return;
    }

    try {
        await buscar(`/api/usuarios/${usuario.id}`, { method: "DELETE" });
        await carregarUsuarios();
    } catch (erro) {
        alert(erro.message);
    }
}

async function salvarUsuarioHandler(event) {
    event.preventDefault();

    const dados = {
        nome: nomeInput.value.trim(),
        email: emailInput.value.trim(),
        matricula: matriculaInput.value.trim(),
        turma: turmaInput.value.trim()
    };

    if (!dados.nome || !dados.email || !dados.matricula) {
        alert("Nome, e-mail e matrícula são obrigatórios.");
        return;
    }

    const id = usuarioIdInput.value;

    salvarUsuario.disabled = true;

    try {
        if (id) {
            await buscar(`/api/usuarios/${id}`, {
                method: "PUT",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(dados)
            });
        } else {
            await buscar("/api/usuarios", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(dados)
            });
        }

        fecharModalUsuario();
        await carregarUsuarios();
    } catch (erro) {
        alert(erro.message);
    } finally {
        salvarUsuario.disabled = false;
    }
}

btnNovoUsuario.addEventListener("click", () => abrirModal());
fecharModal.addEventListener("click", fecharModalUsuario);
cancelarModal.addEventListener("click", fecharModalUsuario);

modalUsuario.addEventListener("click", (event) => {
    if (event.target === modalUsuario) {
        fecharModalUsuario();
    }
});

formUsuario.addEventListener("submit", salvarUsuarioHandler);

buscaUsuario.addEventListener("input", (event) => {
    termoBusca = event.target.value.trim();
    renderizarUsuarios();
});

carregarUsuarios();
