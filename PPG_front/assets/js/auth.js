// ===== INSCRIPTION =====
async function handleRegister(event) {
  event.preventDefault();
  const form = event.target;
  const errorEl = document.getElementById("error-msg");
  const btn = form.querySelector("button[type=submit]");

  btn.disabled = true;
  btn.textContent = "Chargement...";
  errorEl.textContent = "";

  const payload = {
    email: form.email.value.trim(),
    first_name: form.first_name.value.trim(),
    last_name: form.last_name.value.trim(),
    password: form.password.value,
    password_confirm: form.password_confirm.value,
  };

  const res = await api.request("POST", "/auth/register/", payload, false);

  if (!res) {
    errorEl.textContent = "Erreur réseau.";
    btn.disabled = false;
    btn.textContent = "S'inscrire";
    return;
  }

  const data = await res.json();

  if (res.ok) {
    api.saveTokens(data.tokens, data.user);
    window.location.href = "/index.html";
  } else {
    // Affiche les erreurs Django
    const messages = Object.values(data).flat().join(" ");
    errorEl.textContent = messages;
    btn.disabled = false;
    btn.textContent = "S'inscrire";
  }
}

// ===== CONNEXION =====
async function handleLogin(event) {
  event.preventDefault();
  const form = event.target;
  const errorEl = document.getElementById("error-msg");
  const btn = form.querySelector("button[type=submit]");

  btn.disabled = true;
  btn.textContent = "Connexion...";
  errorEl.textContent = "";

  const payload = {
    email: form.email.value.trim(),
    password: form.password.value,
  };

  const res = await api.request("POST", "/auth/login/", payload, false);
  const data = await res.json();

  if (res.ok) {
    api.saveTokens(data.tokens, data.user);
    window.location.href = "/index.html";
  } else {
    errorEl.textContent = data.error || "Identifiants incorrects.";
    btn.disabled = false;
    btn.textContent = "Se connecter";
  }
}

// ===== DÉCONNEXION =====
async function handleLogout() {
  const refresh = localStorage.getItem("refresh_token");
  await api.request("POST", "/auth/logout/", { refresh });
  api.logout();
}