const API_BASE = "http://127.0.0.1:8000/api";

const api = {
  // Récupère le token depuis localStorage
  getAccessToken() {
    return localStorage.getItem("access_token");
  },

  // Headers avec Bearer token
  getHeaders(withAuth = true) {
    const headers = { "Content-Type": "application/json" };
    if (withAuth) {
      const token = this.getAccessToken();
      if (token) headers["Authorization"] = `Bearer ${token}`;
    }
    return headers;
  },

  // Requête générique avec refresh automatique
  async request(method, endpoint, body = null, withAuth = true) {
    const options = {
      method,
      headers: this.getHeaders(withAuth),
    };
    if (body) options.body = JSON.stringify(body);

    let response = await fetch(`${API_BASE}${endpoint}`, options);

    // Si token expiré → essaie de le rafraîchir
    if (response.status === 401 && withAuth) {
      const refreshed = await this.refreshToken();
      if (refreshed) {
        options.headers = this.getHeaders(true);
        response = await fetch(`${API_BASE}${endpoint}`, options);
      } else {
        this.logout();
        return null;
      }
    }

    return response;
  },

  // Rafraîchit le access token
  async refreshToken() {
    const refresh = localStorage.getItem("refresh_token");
    if (!refresh) return false;

    const res = await fetch(`${API_BASE}/auth/token/refresh/`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ refresh }),
    });

    if (res.ok) {
      const data = await res.json();
      localStorage.setItem("access_token", data.access);
      return true;
    }
    return false;
  },

  // Sauvegarde les tokens après login/register
  saveTokens(tokens, user) {
    localStorage.setItem("access_token", tokens.access);
    localStorage.setItem("refresh_token", tokens.refresh);
    localStorage.setItem("user", JSON.stringify(user));
  },

  // Déconnexion côté client
  logout() {
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
    localStorage.removeItem("user");
    window.location.href = "/login.html";
  },

  isAuthenticated() {
    return !!this.getAccessToken();
  },

  getCurrentUser() {
    const user = localStorage.getItem("user");
    return user ? JSON.parse(user) : null;
  },
};