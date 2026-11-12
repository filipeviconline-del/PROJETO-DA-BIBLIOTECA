const registerForm = document.getElementById("registerForm");

const nameInput = document.getElementById("name");
const usernameInput = document.getElementById("username");
const emailInput = document.getElementById("email");
const registrationInput = document.getElementById("registration");
const securityQuestionInput = document.getElementById("securityQuestion");
const securityAnswerInput = document.getElementById("securityAnswer");
const passwordInput = document.getElementById("password");
const confirmPasswordInput = document.getElementById("confirmPassword");
const termsInput = document.getElementById("terms");

const registerButton = document.getElementById("registerButton");
const statusMessage = document.getElementById("statusMessage");
const currentYear = document.getElementById("currentYear");

currentYear.textContent = new Date().getFullYear();

function showError(input, message) {
    input.classList.add("input-error");

    const errorElement = document.getElementById(`${input.id}Error`);

    if (errorElement) {
        errorElement.textContent = message;
    }
}

function clearError(input) {
    input.classList.remove("input-error");

    const errorElement = document.getElementById(`${input.id}Error`);

    if (errorElement) {
        errorElement.textContent = "";
    }
}

function setStatus(message, type) {
    statusMessage.textContent = message;
    statusMessage.className = `status-message ${type}`;
}

function validateEmail(email) {
    return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
}

function validateForm() {
    let isValid = true;

    const fields = [
        nameInput,
        usernameInput,
        emailInput,
        registrationInput,
        passwordInput,
        confirmPasswordInput
    ];

    fields.forEach(clearError);

    document.getElementById("termsError").textContent = "";
    setStatus("", "");

    if (nameInput.value.trim().length < 3) {
        showError(nameInput, "Digite seu nome completo.");
        isValid = false;
    }

    if (usernameInput.value.trim().length < 3) {
        showError(usernameInput, "Informe um usuário válido.");
        isValid = false;
    }

    if (!validateEmail(emailInput.value.trim())) {
        showError(emailInput, "Digite um e-mail válido.");
        isValid = false;
    }

    if (registrationInput.value.trim() === "") {
        showError(registrationInput, "Informe sua matrícula ou código.");
        isValid = false;
    }

    if (securityQuestionInput.value.trim() === "") {
        showError(securityQuestionInput,
            "Escolha uma pergunta de segurança (para recuperar a senha).");
        isValid = false;
    }

    if (securityAnswerInput.value.trim().length < 2) {
        showError(securityAnswerInput, "Informe a resposta de segurança.");
        isValid = false;
    }

    if (passwordInput.value.length < 6) {
        showError(
            passwordInput,
            "A senha deve ter pelo menos 6 caracteres."
        );
        isValid = false;
    }

    if (confirmPasswordInput.value !== passwordInput.value) {
        showError(
            confirmPasswordInput,
            "As senhas não coincidem."
        );
        isValid = false;
    }

    if (!termsInput.checked) {
        document.getElementById("termsError").textContent =
            "Você precisa aceitar os termos de uso.";
        isValid = false;
    }

    return isValid;
}

document.querySelectorAll(".show-password").forEach((button) => {
    button.addEventListener("click", () => {
        const targetId = button.dataset.target;
        const targetInput = document.getElementById(targetId);

        const isPassword = targetInput.type === "password";

        targetInput.type = isPassword ? "text" : "password";
        button.textContent = isPassword ? "Ocultar" : "Mostrar";
    });
});

registerForm.addEventListener("submit", async (event) => {
    event.preventDefault();

    if (!validateForm()) {
        setStatus("Verifique os dados informados.", "error");
        return;
    }

    registerButton.disabled = true;
    registerButton.classList.add("loading");

    try {
        const resposta = await fetch("/api/auth/cadastro", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                nome: nameInput.value.trim(),
                usuario: usernameInput.value.trim(),
                email: emailInput.value.trim(),
                matricula: registrationInput.value.trim(),
                senha: passwordInput.value,
                pergunta_seguranca: securityQuestionInput.value.trim(),
                resposta_seguranca: securityAnswerInput.value.trim(),
            }),
        });

        const dados = await resposta.json();

        if (!resposta.ok) {
            setStatus(dados.erro || "Erro ao criar conta.", "error");
            registerButton.disabled = false;
            registerButton.classList.remove("loading");
            return;
        }

        // Salva dados da sessão no localStorage
        localStorage.setItem("toschibook_usuario", JSON.stringify(dados.conta));

        setStatus("Conta criada com sucesso! Redirecionando...", "success");

        // Redireciona para o dashboard após cadastro bem-sucedido
        setTimeout(() => {
            window.location.href = "dashboard.html";
        }, 1000);

    } catch (erro) {
        setStatus("Erro de conexão com o servidor.", "error");
        registerButton.disabled = false;
        registerButton.classList.remove("loading");
    }
});

[
    nameInput,
    usernameInput,
    emailInput,
    registrationInput,
    securityAnswerInput,
    passwordInput,
    confirmPasswordInput
].forEach((input) => {
    input.addEventListener("input", () => {
        clearError(input);
        setStatus("", "");
    });
});

securityQuestionInput.addEventListener("change", () => {
    clearError(securityQuestionInput);
    setStatus("", "");
});

termsInput.addEventListener("change", () => {
    document.getElementById("termsError").textContent = "";
    setStatus("", "");
});