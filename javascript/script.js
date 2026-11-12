const loginForm = document.getElementById("loginForm");
const emailInput = document.getElementById("email");
const passwordInput = document.getElementById("password");

const emailError = document.getElementById("emailError");
const passwordError = document.getElementById("passwordError");

const togglePassword = document.getElementById("togglePassword");
const loginButton = document.getElementById("loginButton");
const statusMessage = document.getElementById("statusMessage");
const forgotPassword = document.getElementById("forgotPassword");
const currentYear = document.getElementById("currentYear");

currentYear.textContent = new Date().getFullYear();

function showError(input, errorElement, message) {
    input.classList.add("input-error");
    errorElement.textContent = message;
}

function clearError(input, errorElement) {
    input.classList.remove("input-error");
    errorElement.textContent = "";
}

function clearStatus() {
    statusMessage.textContent = "";
    statusMessage.className = "status-message";
}

function validateForm() {
    let isValid = true;

    clearError(emailInput, emailError);
    clearError(passwordInput, passwordError);
    clearStatus();

    const emailValue = emailInput.value.trim();
    const passwordValue = passwordInput.value.trim();

    if (emailValue === "") {
        showError(
            emailInput,
            emailError,
            "Informe seu e-mail ou usuário."
        );

        isValid = false;
    }

    if (passwordValue === "") {
        showError(
            passwordInput,
            passwordError,
            "Informe sua senha."
        );

        isValid = false;
    } else if (passwordValue.length < 4) {
        showError(
            passwordInput,
            passwordError,
            "A senha deve ter pelo menos 4 caracteres."
        );

        isValid = false;
    }

    return isValid;
}

togglePassword.addEventListener("click", () => {
    const isPassword = passwordInput.type === "password";

    passwordInput.type = isPassword ? "text" : "password";
    togglePassword.textContent = isPassword ? "Ocultar" : "Mostrar";
    togglePassword.setAttribute(
        "aria-label",
        isPassword ? "Ocultar senha" : "Mostrar senha"
    );
});

loginForm.addEventListener("submit", async (event) => {
    event.preventDefault();

    if (!validateForm()) {
        return;
    }

    loginButton.disabled = true;
    loginButton.classList.add("loading");

    try {
        const resposta = await fetch("/api/auth/login", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                identificador: emailInput.value.trim(),
                senha: passwordInput.value,
            }),
        });

        const dados = await resposta.json();

        if (!resposta.ok) {
            statusMessage.textContent = dados.erro || "Erro ao realizar login.";
            statusMessage.classList.add("error");
            loginButton.disabled = false;
            loginButton.classList.remove("loading");
            return;
        }

        // Salva dados da sessão no localStorage para uso no frontend
        localStorage.setItem("toschibook_usuario", JSON.stringify(dados.conta));

        statusMessage.textContent = "Login realizado com sucesso!";
        statusMessage.classList.add("success");

        // Redireciona para a tela inicial (dashboard)
        setTimeout(() => {
            window.location.href = "dashboard.html";
        }, 600);

    } catch (erro) {
        statusMessage.textContent = "Erro de conexão com o servidor.";
        statusMessage.classList.add("error");
        loginButton.disabled = false;
        loginButton.classList.remove("loading");
    }
});

forgotPassword.addEventListener("click", (event) => {
    event.preventDefault();
    // Leva para a tela de recuperação por pergunta de segurança.
    window.location.href = "recuperar.html";
});

emailInput.addEventListener("input", () => {
    clearError(emailInput, emailError);
    clearStatus();
});

passwordInput.addEventListener("input", () => {
    clearError(passwordInput, passwordError);
    clearStatus();
});
