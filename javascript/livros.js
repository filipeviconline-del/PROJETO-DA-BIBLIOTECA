/* ===== Página de Livros - ToschiBook ===== */

const btnNovoLivro = document.getElementById("btnNovoLivro");
const buscaLivro = document.getElementById("buscaLivro");
const livrosCount = document.getElementById("livrosCount");
const livrosEmpty = document.getElementById("livrosEmpty");
const livrosGrid = document.getElementById("livrosGrid");

const modalLivro = document.getElementById("modalLivro");
const modalTitulo = document.getElementById("modalTitulo");
const fecharModal = document.getElementById("fecharModal");
const cancelarModal = document.getElementById("cancelarModal");
const formLivro = document.getElementById("formLivro");
const livroIdInput = document.getElementById("livroId");
const tituloInput = document.getElementById("titulo");
const autorInput = document.getElementById("autor");
const anoInput = document.getElementById("ano");
const quantidadeInput = document.getElementById("quantidade");
const categoriaInput = document.getElementById("categoria");
const salvarLivro = document.getElementById("salvarLivro");

// Upload de capa
const capaInput = document.getElementById("capaInput");
const capaUploadArea = document.getElementById("capaUploadArea");
const capaPreview = document.getElementById("capaPreview");

let livros = [];
let termoBusca = "";
let capaArquivo = null;

// --- Upload de capa: click, drag & drop ---

capaUploadArea.addEventListener("click", () => capaInput.click());

capaUploadArea.addEventListener("dragover", (e) => {
    e.preventDefault();
    capaUploadArea.classList.add("drag-over");
});

capaUploadArea.addEventListener("dragleave", () => {
    capaUploadArea.classList.remove("drag-over");
});

capaUploadArea.addEventListener("drop", (e) => {
    e.preventDefault();
    capaUploadArea.classList.remove("drag-over");
    const file = e.dataTransfer.files[0];
    if (file && file.type.startsWith("image/")) {
        capaArquivo = file;
        mostrarPreviewCapa(file);
    }
});

capaInput.addEventListener("change", () => {
    const file = capaInput.files[0];
    if (file) {
        capaArquivo = file;
        mostrarPreviewCapa(file);
    }
});

function mostrarPreviewCapa(file) {
    const reader = new FileReader();
    reader.onload = (e) => {
        capaPreview.innerHTML = `
            <img src="${e.target.result}" alt="Preview da capa">
            <span class="capa-change-hint">Clique para trocar a capa</span>
        `;
    };
    reader.readAsDataURL(file);
}

function resetPreviewCapa(capaUrl) {
    if (capaUrl) {
        capaPreview.innerHTML = `
            <img src="${capaUrl}" alt="Capa do livro">
            <span class="capa-change-hint">Clique para trocar a capa</span>
        `;
    } else {
        capaPreview.innerHTML = `
            <span class="capa-placeholder"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="icon-svg"><path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z"/><circle cx="12" cy="13" r="4"/></svg></span>
            <p>Clique ou arraste para adicionar a capa</p>
        `;
    }
}

// --- Funções auxiliares ---

async function buscarApi(url, opcoes) {
    const resposta = await fetch(apiUrl(url), opcoes);

    if (!resposta.ok) {
        const erro = await resposta.json().catch(() => ({}));
        throw new Error(erro.erro || `Erro ${resposta.status}`);
    }

    return resposta.json();
}

function formatarSigla(titulo) {
    const palavras = titulo.trim().split(/\s+/).filter(Boolean);
    return palavras.slice(0, 2).map((p) => p[0].toUpperCase()).join("") || '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="icon-svg"><path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/></svg>';
}

// --- Modal ---

function abrirModal(livro = null) {
    modalTitulo.textContent = livro ? "Editar livro" : "Novo livro";
    livroIdInput.value = livro ? livro.id : "";

    tituloInput.value = livro ? livro.titulo : "";
    autorInput.value = livro ? livro.autor : "";
    anoInput.value = livro ? livro.ano ?? "" : "";
    quantidadeInput.value = livro ? livro.quantidade ?? 1 : 1;
    categoriaInput.value = livro ? livro.categoria ?? "" : "";

    capaArquivo = null;
    capaInput.value = "";

    if (livro && livro.capa) {
        resetPreviewCapa(apiUrl(`/api/uploads/${livro.capa}`));
    } else {
        resetPreviewCapa(null);
    }

    modalLivro.hidden = false;
    tituloInput.focus();
}

function fecharModalLivro() {
    modalLivro.hidden = true;
    formLivro.reset();
    capaArquivo = null;
    resetPreviewCapa(null);
}

// --- Erro ---

function mostrarErro(mensagem) {
    livrosGrid.innerHTML = "";
    livrosEmpty.hidden = false;
    livrosEmpty.innerHTML = "";

    const aviso = document.createElement("div");
    aviso.className = "load-error";
    aviso.textContent = mensagem;
    livrosEmpty.appendChild(aviso);
}

// --- Renderizar cards ---

function renderizarLivros() {
    const filtrados = livros.filter((livro) => {
        if (!termoBusca) return true;
        const termo = termoBusca.toLowerCase();
        return (
            livro.titulo.toLowerCase().includes(termo) ||
            livro.autor.toLowerCase().includes(termo)
        );
    });

    livrosCount.textContent = `${filtrados.length} registro(s)`;

    const temLivros = filtrados.length > 0;
    livrosEmpty.hidden = temLivros;

    if (!temLivros) {
        livrosGrid.innerHTML = "";
        livrosEmpty.innerHTML = "";
        const icone = document.createElement("span");
        icone.className = "empty-icon";
        icone.innerHTML = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="icon-svg"><path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/></svg>';

        const texto = document.createElement("p");
        texto.textContent = termoBusca
            ? "Nenhum livro encontrado para esta busca."
            : "Nenhum livro cadastrado ainda.";

        livrosEmpty.append(icone, texto);
        return;
    }

    livrosGrid.innerHTML = "";

    filtrados.forEach((livro) => {
        const disponiveis = livro.disponiveis ?? livro.quantidade ?? 1;
        const estaDisponivel = disponiveis > 0;
        const statusClass = estaDisponivel ? "disponivel" : "indisponivel";

        const card = document.createElement("article");
        card.className = `book-card ${statusClass}`;

        // -- Capa --
        const coverDiv = document.createElement("div");
        coverDiv.className = "book-card-cover";

        // Badge de disponibilidade
        const badge = document.createElement("span");
        badge.className = `availability-badge ${statusClass}`;
        badge.textContent = estaDisponivel
            ? `${disponiveis} disponíve${disponiveis === 1 ? "l" : "is"}`
            : "Indisponível";
        coverDiv.appendChild(badge);

        if (livro.capa) {
            const img = document.createElement("img");
            img.src = apiUrl(`/api/uploads/${livro.capa}`);
            img.alt = `Capa de ${livro.titulo}`;
            img.loading = "lazy";
            coverDiv.appendChild(img);
        } else {
            const placeholder = document.createElement("div");
            placeholder.className = "cover-placeholder";

            const siglaSpan = document.createElement("span");
            siglaSpan.className = "cover-sigla";
            siglaSpan.textContent = formatarSigla(livro.titulo);

            const iconSpan = document.createElement("span");
            iconSpan.className = "cover-icon";
            iconSpan.innerHTML = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="icon-svg"><path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/></svg>';

            placeholder.append(iconSpan, siglaSpan);
            coverDiv.appendChild(placeholder);
        }

        // -- Info --
        const infoDiv = document.createElement("div");
        infoDiv.className = "book-card-info";

        const title = document.createElement("h3");
        title.className = "book-card-title";
        title.textContent = livro.titulo;

        const author = document.createElement("p");
        author.className = "book-card-author";
        author.textContent = livro.autor;

        infoDiv.append(title, author);

        // Meta (categoria + ano)
        if (livro.categoria || livro.ano) {
            const metaDiv = document.createElement("div");
            metaDiv.className = "book-card-meta";

            if (livro.categoria) {
                const cat = document.createElement("span");
                cat.className = "book-card-category";
                cat.textContent = livro.categoria;
                metaDiv.appendChild(cat);
            }

            if (livro.ano) {
                const year = document.createElement("span");
                year.className = "book-card-year";
                year.textContent = livro.ano;
                metaDiv.appendChild(year);
            }

            infoDiv.appendChild(metaDiv);
        }

        // Quantidade
        const qty = document.createElement("p");
        qty.className = "book-card-qty";
        const total = livro.quantidade ?? 1;
        qty.textContent = `${total} exemplar${total !== 1 ? "es" : ""} no acervo`;
        infoDiv.appendChild(qty);

        // -- Ações --
        const actionsDiv = document.createElement("div");
        actionsDiv.className = "book-card-actions";

        const btnEditar = document.createElement("button");
        btnEditar.type = "button";
        btnEditar.className = "btn btn-secondary btn-small";
        btnEditar.innerHTML = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="icon-svg"><path d="M17 3a2.828 2.828 0 1 1 4 4L7.5 20.5 2 22l1.5-5.5L17 3z"/></svg>' + " Editar";
        btnEditar.addEventListener("click", () => abrirModal(livro));

        const btnExcluir = document.createElement("button");
        btnExcluir.type = "button";
        btnExcluir.className = "btn btn-danger btn-small";
        btnExcluir.innerHTML = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="icon-svg"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/><line x1="10" y1="11" x2="10" y2="17"/><line x1="14" y1="11" x2="14" y2="17"/></svg>' + " Excluir";
        btnExcluir.addEventListener("click", () => excluirLivro(livro));

        actionsDiv.append(btnEditar, btnExcluir);

        card.append(coverDiv, infoDiv, actionsDiv);
        livrosGrid.appendChild(card);
    });
}

// --- API ---

async function carregarLivros() {
    try {
        livros = await buscarApi("/api/livros");
        renderizarLivros();
    } catch (erro) {
        mostrarErro("Não foi possível carregar os livros. Verifique se o servidor está rodando.");
    }
}

async function excluirLivro(livro) {
    const confirmacao = confirm(`Excluir o livro "${livro.titulo}"?`);
    if (!confirmacao) return;

    try {
        await buscarApi(`/api/livros/${livro.id}`, { method: "DELETE" });
        await carregarLivros();
    } catch (erro) {
        alert(erro.message);
    }
}

async function salvarLivroHandler(event) {
    event.preventDefault();

    const titulo = tituloInput.value.trim();
    const autor = autorInput.value.trim();

    if (!titulo || !autor) {
        alert("Título e autor são obrigatórios.");
        return;
    }

    const id = livroIdInput.value;
    salvarLivro.disabled = true;

    try {
        // Usa FormData para enviar arquivo junto com dados
        const formData = new FormData();
        formData.append("titulo", titulo);
        formData.append("autor", autor);
        formData.append("ano", anoInput.value || "");
        formData.append("quantidade", quantidadeInput.value || "1");
        formData.append("categoria", categoriaInput.value.trim());

        if (capaArquivo) {
            formData.append("capa", capaArquivo);
        }

        if (id) {
            await fetch(apiUrl(`/api/livros/${id}`), {
                method: "PUT",
                body: formData,
            }).then(async (r) => {
                if (!r.ok) {
                    const e = await r.json().catch(() => ({}));
                    throw new Error(e.erro || `Erro ${r.status}`);
                }
            });
        } else {
            await fetch(apiUrl("/api/livros"), {
                method: "POST",
                body: formData,
            }).then(async (r) => {
                if (!r.ok) {
                    const e = await r.json().catch(() => ({}));
                    throw new Error(e.erro || `Erro ${r.status}`);
                }
            });
        }

        fecharModalLivro();
        await carregarLivros();
    } catch (erro) {
        alert(erro.message);
    } finally {
        salvarLivro.disabled = false;
    }
}

// --- Event listeners ---

btnNovoLivro.addEventListener("click", () => abrirModal());
fecharModal.addEventListener("click", fecharModalLivro);
cancelarModal.addEventListener("click", fecharModalLivro);

modalLivro.addEventListener("click", (event) => {
    if (event.target === modalLivro) {
        fecharModalLivro();
    }
});

formLivro.addEventListener("submit", salvarLivroHandler);

buscaLivro.addEventListener("input", (event) => {
    termoBusca = event.target.value.trim();
    renderizarLivros();
});

carregarLivros();
