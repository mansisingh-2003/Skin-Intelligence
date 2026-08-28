const TOKEN_KEY = "skin_intelligence_token";
const USER_KEY = "skin_intelligence_user";

/* =========================================================
   TOKEN
========================================================= */

export function saveToken(token) {
  if (!token) return;

  localStorage.setItem(TOKEN_KEY, token);
}

export function getToken() {
  return localStorage.getItem(TOKEN_KEY);
}

export function removeToken() {
  localStorage.removeItem(TOKEN_KEY);
}


/* =========================================================
   USER
========================================================= */

export function saveUser(user) {
  if (!user) return;

  localStorage.setItem(
    USER_KEY,
    JSON.stringify(user)
  );
}

export function getSavedUser() {
  try {
    const user = localStorage.getItem(USER_KEY);

    return user
      ? JSON.parse(user)
      : null;
  } catch {
    return null;
  }
}

export function removeSavedUser() {
  localStorage.removeItem(USER_KEY);
}


/* =========================================================
   AUTH STATUS
========================================================= */

export function isLoggedIn() {
  return Boolean(getToken());
}


/* =========================================================
   LOGOUT
========================================================= */

export function logout() {
  removeToken();
  removeSavedUser();
}


/*
   App.jsx currently uses clearAuth().
   Keep this alias so we don't have to
   rewrite the existing App.jsx yet.
*/

export function clearAuth() {
  logout();
}


/* =========================================================
   AUTH HEADERS
========================================================= */

export function getAuthHeaders() {
  const token = getToken();

  if (!token) {
    return {};
  }

  return {
    Authorization: `Bearer ${token}`,
  };
}