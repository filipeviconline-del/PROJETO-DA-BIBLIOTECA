<div align="center">

<img src="https://capsule-render.vercel.app/api?type=waving&color=0:1e3a8a,100:38bdf8&height=220&section=header&text=Sistema%20Bibliotecário&fontSize=42&fontColor=ffffff&animation=fadeIn&fontAlignY=35" width="100%"/>

<br>

<img src="https://readme-typing-svg.demolab.com?font=Fira+Code&size=22&pause=1000&color=38BDF8&center=true&vCenter=true&width=700&lines=Gerenciamento+inteligente+de+bibliotecas;Controle+de+livros%2C+leitores+e+empr%C3%A9stimos;Projeto+desenvolvido+em+equipe+com+Python" alt="Texto animado"/>

<br><br>

<img src="https://img.shields.io/badge/Python-3.11%2B-3776AB?style=for-the-badge&logo=python&logoColor=white"/>
<img src="https://img.shields.io/badge/PySide6-Interface-41CD52?style=for-the-badge&logo=qt&logoColor=white"/>
<img src="https://img.shields.io/badge/SQLite-Banco_de_dados-003B57?style=for-the-badge&logo=sqlite&logoColor=white"/>
<img src="https://img.shields.io/badge/Status-Em_desenvolvimento-orange?style=for-the-badge"/>

</div>

---

## 📚 Sobre o projeto

O **Sistema Bibliotecário** é uma aplicação desenvolvida em Python para auxiliar no gerenciamento completo de uma biblioteca.

O sistema foi projetado para organizar o acervo, controlar leitores, registrar empréstimos e devoluções, administrar reservas, calcular multas e gerar relatórios.

A aplicação está sendo desenvolvida por uma equipe utilizando boas práticas de programação, controle de versões e divisão de responsabilidades.

---

## ✨ Demonstração das funcionalidades

<div align="center">

| 📖 Livros | 👥 Leitores | 🔄 Empréstimos |
|:---:|:---:|:---:|
| Cadastro e pesquisa de livros | Controle dos leitores | Registro de empréstimos |
| Controle de exemplares | Histórico de movimentações | Controle de prazos |

| 📌 Reservas | 💰 Multas | 📊 Relatórios |
|:---:|:---:|:---:|
| Fila de reservas | Cálculo automático | PDF e Excel |
| Controle de disponibilidade | Registro de pagamentos | Indicadores do sistema |

</div>

---

## 🎯 Funcionalidades

### 📖 Gerenciamento de livros

- Cadastro de livros;
- Cadastro de autores;
- Cadastro de editoras;
- Cadastro de categorias;
- Cadastro de exemplares;
- Pesquisa por título, ISBN ou autor;
- Controle de disponibilidade;
- Controle de localização;
- Registro de livros perdidos ou danificados.

### 👥 Gerenciamento de leitores

- Cadastro de leitores;
- Edição de dados;
- Controle de leitores ativos e bloqueados;
- Histórico de empréstimos;
- Controle de limite de livros;
- Pesquisa por nome, documento ou e-mail.

### 🔄 Empréstimos e devoluções

- Registro de empréstimos;
- Registro de devoluções;
- Controle de data prevista;
- Identificação de atrasos;
- Renovação de empréstimos;
- Cálculo automático de multas;
- Atualização automática dos exemplares.

### 📌 Reservas

- Reserva de livros indisponíveis;
- Controle da fila de espera;
- Cancelamento de reservas;
- Controle do prazo de retirada;
- Atualização automática da disponibilidade.

### 💰 Multas

- Multas por atraso;
- Multas por dano;
- Multas por perda;
- Registro de pagamentos;
- Controle de valores em aberto;
- Histórico financeiro dos leitores.

### 📊 Relatórios

- Livros mais emprestados;
- Leitores mais ativos;
- Empréstimos atrasados;
- Multas em aberto;
- Inventário do acervo;
- Empréstimos por período;
- Exportação para PDF;
- Exportação para Excel.

---

## 🛠️ Tecnologias utilizadas

<div align="center">

<img src="https://skillicons.dev/icons?i=python,sqlite,git,github,vscode" />

</div>

<br>

- **Python** — Linguagem principal;
- **PySide6** — Interface gráfica;
- **SQLAlchemy** — Comunicação com o banco de dados;
- **SQLite** — Banco de dados local;
- **PostgreSQL** — Opção para ambiente em rede;
- **ReportLab** — Geração de relatórios em PDF;
- **OpenPyXL** — Exportação para Excel;
- **PyInstaller** — Criação do executável;
- **GitHub** — Controle de versão e colaboração.

---

 
---

## 🚀 Instalação e execução

O ToschiBook é uma aplicação web local (servidor **Flask** + interface no navegador).

### Opção A — Instalador gráfico (assistente) ⭐ recomendado

Um assistente visual no estilo *Avançar → Avançar → Concluir*, com a identidade
do ToschiBook (logo e cores verdes), que copia o programa, prepara o ambiente,
instala as dependências e cria atalhos — tudo com cliques.

```bash
python3 instalador_grafico.py
# atalhos:  ./instalador.sh  (Linux/macOS)  |  instalador.bat  (Windows)
```

Passos do assistente: **boas-vindas → termos → pasta de instalação → opções de
atalho → número de série → instalação (com barra de progresso) → concluir**
(com opção de iniciar o sistema). Ele também gera um **desinstalador** na pasta
instalada.

Na etapa **número de série**, você já pode **ativar o produto durante a
instalação**: o serial é formatado e validado offline enquanto você digita, e a
ativação é gravada direto no banco da instalação. O campo é opcional — se ficar
em branco, o sistema pede o serial no primeiro acesso.

> 🐧 **Linux:** o instalador gráfico usa Tkinter. Se faltar, instale uma vez:
> `sudo apt install python3-tk` (Debian/Ubuntu/Mint) ou
> `sudo dnf install python3-tkinter` (Fedora). No Windows e macOS o Tkinter já
> vem com o Python.

### Opção B — Rodar a partir do código-fonte (linha de comando)

```bash
# 1. Clone o repositório e entre na pasta
cd PROJETO-DA-BIBLIOTECA

# 2. Instale tudo e inicie (abre o navegador automaticamente)
python instalar.py
```

O `instalar.py` faz tudo automaticamente:

1. verifica a versão do Python;
2. **cria um ambiente virtual (`.venv`)** e se reexecuta dentro dele — assim já
   resolve sozinho o erro `externally-managed-environment` (PEP 668) do Linux,
   sem você precisar digitar nada;
3. instala as dependências do `requirements.txt` no `.venv`;
4. inicializa o banco e abre o sistema em `http://127.0.0.1:5000`.

Para apenas preparar o ambiente, sem iniciar: `python3 instalar.py --sem-iniciar`.
Para instalar no Python atual, sem criar um venv: `python3 instalar.py --sem-venv`.

**Para iniciar novamente depois**, use o Python do ambiente virtual:

```bash
# Linux/macOS
.venv/bin/python iniciar.py
# Windows
.venv\Scripts\python iniciar.py
```

> 🐧 Se a criação do venv falhar no Debian/Ubuntu/Mint, instale-o uma vez:
> `sudo apt install python3-venv python3-full` e rode de novo.

### Opção C — Gerar o executável / instalador

```bash
# Instala dependências e empacota com o PyInstaller
python build.py
# (ou, atalhos:  build.bat  no Windows  /  ./build.sh  no Linux/macOS)
```

O executável é gerado em `dist/ToschiBook` (ou `dist\ToschiBook.exe` no Windows).

**Instalador Windows (opcional):** com o [Inno Setup](https://jrsoftware.org/isdl.php)
instalado, compile o `instalador.iss` para gerar `Output\ToschiBook-Setup.exe`,
um instalador com atalhos no Menu Iniciar e na Área de Trabalho.

---

## 🔑 Ativação por número de série

O sistema exige um **serial válido** para ser usado. Enquanto não estiver
ativado, qualquer página é redirecionada para a tela de ativação
(`/html/ativacao.html`) e a API responde `403`.

### Como funciona

- O serial tem o formato `XXXXX-XXXXX-XXXXX-XXXXX-XXXXX`.
- Ele é **assinado criptograficamente (HMAC-SHA256)** e carrega, de forma
  embutida, o tipo da licença, a validade e o **limite de ativações** — por isso
  a validação é **offline**, sem precisar de servidor de licenças.
- Ao ativar, a licença é **vinculada ao computador** (fingerprint de hardware) e
  guardada no banco. Um serial ativado numa máquina não vale em outra.
- Licenças com prazo (`trial`, `mensal`, `anual`, etc.) têm **data de expiração**;
  `perpetua`/`vitalicia` não expiram.

### Tipos de licença

| Tipo | Validade | Ativações (padrão) |
|---|---|---|
| `trial` | 30 dias | 1 |
| `mensal` | 30 dias | 1 |
| `trimestral` | 90 dias | 1 |
| `semestral` | 180 dias | 2 |
| `anual` | 365 dias | 3 |
| `bienal` | 730 dias | 3 |
| `perpetua` | perpétua | 1 |
| `vitalicia` | perpétua | 1 |
| `educacional` | 365 dias | 30 |
| `corporativa` | 365 dias | 100 |

Veja a tabela a qualquer momento com `python gerar_serial.py --listar-tipos`.

### Limite de ativações

Cada serial permite ser ativado em um número máximo de **máquinas distintas**,
embutido e assinado no próprio serial (`0` = ilimitado). Reativar na mesma
máquina **não** consome uma nova ativação; ao atingir o limite, novas máquinas
são recusadas com uma mensagem clara.

> ℹ️ Como o sistema é **offline** (cada instalação tem seu próprio banco), a
> contagem de ativações é mantida **localmente por instalação**. Para um controle
> global de ativações entre computadores seria necessário um servidor de licenças.

### Gerar seriais (uso administrativo)

Quem vende/administra as licenças usa o `gerar_serial.py`:

```bash
# 1 serial perpétuo
python gerar_serial.py

# 5 seriais anuais
python gerar_serial.py --tipo anual --quantidade 5

# trial de 15 dias
python gerar_serial.py --tipo trial --dias 15

# licença corporativa com até 50 máquinas
python gerar_serial.py --tipo corporativa --ativacoes 50

# ativações ilimitadas
python gerar_serial.py --tipo perpetua --ativacoes 0

# listar os tipos de licença
python gerar_serial.py --listar-tipos

# validar um serial existente
python gerar_serial.py --validar XXXXX-XXXXX-XXXXX-XXXXX-XXXXX
```

> ⚠️ **Segurança:** a assinatura depende da chave secreta. Em produção, defina
> a variável de ambiente `TOSCHIBOOK_LICENSE_KEY` com um valor forte — **a mesma**
> no gerador e no produto. Não distribua o `gerar_serial.py` com o produto final.

### 🏭 Central de emissão de seriais (`gerador_serial.py`) — anti-cracker

Para uso profissional, prefira a **central de emissão** — uma ferramenta mais
robusta que gerencia a chave, registra tudo o que é emitido e tem menu interativo:

```bash
# 1) Primeiro uso: cria uma CHAVE MESTRA forte e aleatória (salva em licenca.key)
python gerador_serial.py chave --criar

# 2) Emite seriais (registrados em um log assinado), vinculados a um cliente
python gerador_serial.py emitir --tipo anual -q 5 --cliente "Escola Modelo"

# 3) Consulta o histórico do que já foi emitido (com verificação de integridade)
python gerador_serial.py historico

# 4) Valida um serial / exporta o histórico para CSV
python gerador_serial.py validar XXXXX-XXXXX-XXXXX-XXXXX-XXXXX
python gerador_serial.py exportar --saida seriais.csv

# 5) Sem argumentos: abre um MENU interativo
python gerador_serial.py
```

Recursos de segurança da central:

- **Chave mestra forte gerada automaticamente** e salva fora do código em
  `licenca.key` (permissão `600`); exibe uma **impressão digital** da chave para
  você conferir que o produto usa a mesma (sem expor o segredo).
- **Recusa emitir seriais reais com a chave padrão** insegura (use `--forcar`
  só em testes).
- **Log de emissões assinado** (`seriais_emitidos.jsonl`): cada serial fica
  registrado com tipo, validade, limite, data e cliente — e o `historico`
  acusa se alguma linha foi adulterada.

> 🔒 `licenca.key`, `seriais_emitidos.jsonl` e CSVs exportados são **segredos/dados
> de venda** e já estão no `.gitignore` — **nunca** os versione nem distribua.
> Para o produto validar os seriais, use a MESMA chave: aponte
> `TOSCHIBOOK_LICENSE_KEY_FILE` para o `licenca.key` ou defina
> `TOSCHIBOOK_LICENSE_KEY` com o conteúdo dele.

### 🔐 Proteções contra cracking

O módulo `seguranca.py` adiciona camadas que dificultam a adulteração das
licenças (tudo com a biblioteca padrão, sem dependências extras):

- **Chave fora do código-fonte** — a chave mestra é lida de
  `TOSCHIBOOK_LICENSE_KEY` (ou de um arquivo em `TOSCHIBOOK_LICENSE_KEY_FILE`).
  Se o produto rodar com a chave padrão de desenvolvimento, ele **avisa** no log
  e no gerador. Sub-chaves derivadas (*domain separation*) isolam a assinatura
  do serial da assinatura do estado e do relógio.
- **Anti-adulteração do banco** — o registro da licença e cada ativação são
  assinados (HMAC-SHA256). Se alguém **editar o `biblioteca.db`** (p. ex.
  esticar `expira_em`, trocar a máquina ou inserir ativações falsas para furar o
  limite), a assinatura não confere e a licença é recusada (`motivo: adulterada`)
  ou o registro forjado **não conta** como ativação.
- **Anti clock-rollback** — um registro assinado guarda o maior horário já visto.
  Se o usuário **atrasar o relógio** para driblar a validade, o sistema detecta e
  bloqueia (`motivo: relogio_alterado`).

> ℹ️ Nenhuma proteção *client-side* é 100% inviolável contra quem controla
> totalmente a máquina — o objetivo é **elevar muito o custo** do ataque
> (edição de banco, falsificação de serial e manipulação de relógio deixam de
> funcionar com edições triviais). Para garantias fortes de revogação e
> contagem global de ativações, seria necessário um servidor de licenças.

### Painel administrativo de ativações

Depois de logar, acesse **Ativações** na barra lateral (`/html/admin.html`) para:

- ver, em um **banner de status bem visível**, se o produto está **ativado**,
  com os **dias restantes** e uma **barra de progresso** da validade (fica
  amarelo quando faltam 15 dias ou menos, e vermelho se a licença expirou);
- ver a **licença atual** desta máquina (tipo, validade, ativações usadas/limite e o ID da máquina);
- consultar o **resumo por serial** (quantas máquinas cada serial ativou e quantas vagas restam);
- listar todas as **máquinas ativadas**, identificando qual é a máquina atual;
- **revogar** uma ativação para liberar uma vaga do serial (revogar a própria máquina exige reativação).

> 🔒 Os endpoints do painel exigem uma **sessão de usuário logada** (retornam `401` caso contrário).

### Endpoints de licença

| Método | Rota | Descrição |
|---|---|---|
| `GET` | `/api/licenca/status` | Estado atual da licença |
| `GET` | `/api/licenca/maquina` | ID desta máquina (para suporte) |
| `POST` | `/api/licenca/ativar` | Ativa com `{ "serial": "..." }` |
| `GET` | `/api/licenca/ativacoes` | Lista ativações e resumo por serial (requer login) |
| `DELETE` | `/api/licenca/ativacoes/{id}` | Revoga uma ativação (requer login) |
