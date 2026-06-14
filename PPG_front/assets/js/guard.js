// À inclure sur toutes les pages qui nécessitent une connexion
(function () {
  if (!api.isAuthenticated()) {
    window.location.href = "/login.html";
    return;
  }

  // Affiche le nom de l'utilisateur si présent dans la page
  const userNameEl = document.getElementById("user-name");
  if (userNameEl) {
    const user = api.getCurrentUser();
    userNameEl.textContent = user ? user.full_name : "";
  }
})();