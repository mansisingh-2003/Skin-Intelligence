import {
  getToken,
  removeToken,
  saveToken,
  saveUser,
} from "../auth";


// =========================================================
// API CONFIGURATION
// =========================================================

export const API_BASE_URL =
  import.meta.env.VITE_API_URL ||
  "http://127.0.0.1:8000";


// =========================================================
// COMMON REQUEST FUNCTION
// =========================================================

async function request(endpoint, options = {}) {

  const token = getToken();

  const headers = {
    ...(options.headers || {}),
  };


  // -------------------------------------------------------
  // JSON CONTENT TYPE
  // -------------------------------------------------------

  if (!(options.body instanceof FormData)) {

    headers["Content-Type"] =
      "application/json";
  }


  // -------------------------------------------------------
  // JWT AUTHORIZATION
  // -------------------------------------------------------

  if (token) {

    headers["Authorization"] =
      `Bearer ${token}`;
  }


  // -------------------------------------------------------
  // SEND REQUEST
  // -------------------------------------------------------

  let response;

  try {

    response = await fetch(
      `${API_BASE_URL}${endpoint}`,
      {
        ...options,
        headers,
      }
    );

  } catch (error) {

    const networkError = new Error(
      "Unable to connect to the backend server."
    );

    networkError.status = 0;

    throw networkError;
  }


  // -------------------------------------------------------
  // AUTHENTICATION FAILURE
  // -------------------------------------------------------

  if (response.status === 401) {

    removeToken();

    const error = new Error(
      "Your session has expired. Please log in again."
    );

    error.status = 401;

    throw error;
  }


  // -------------------------------------------------------
  // READ RESPONSE
  // -------------------------------------------------------

  const contentType =
    response.headers.get(
      "content-type"
    ) || "";

  let data;


  if (
    contentType.includes(
      "application/json"
    )
  ) {

    data = await response.json();

  } else {

    data = await response.text();
  }


  // -------------------------------------------------------
  // HANDLE BACKEND ERROR
  // -------------------------------------------------------

  if (!response.ok) {

    let message =
      "Request failed.";

    if (
      typeof data === "object" &&
      data !== null
    ) {

      message =
        data.detail ||
        data.message ||
        "Request failed.";

    } else if (data) {

      message = data;
    }


    const error =
      new Error(message);

    error.status =
      response.status;

    error.data = data;

    throw error;
  }


  // -------------------------------------------------------
  // SUCCESS
  // -------------------------------------------------------

  return data;
}


// =========================================================
// AUTHENTICATION
// =========================================================

export async function login(
  email,
  password
) {

  const data = await request(
    "/login",
    {
      method: "POST",

      body: JSON.stringify({
        email,
        password,
      }),
    }
  );


  // -------------------------------------------------------
  // SAVE JWT
  // -------------------------------------------------------

  if (data?.access_token) {

    saveToken(
      data.access_token
    );

  } else if (data?.token) {

    // Fallback in case backend returns "token"
    saveToken(
      data.token
    );
  }


  // -------------------------------------------------------
  // SAVE USER
  // -------------------------------------------------------

  if (data?.user) {

    saveUser(
      data.user
    );
  }


  return data;
}


export async function register(
  userData
) {

  return request(
    "/register",
    {
      method: "POST",

      body: JSON.stringify(
        userData
      ),
    }
  );
}


export async function getMe() {

  return request(
    "/me"
  );
}


// =========================================================
// SKIN PROFILE
// =========================================================

export async function getSkinProfile() {

  return request(
    "/skin-profile"
  );
}


export async function createSkinProfile(
  profile
) {

  return request(
    "/skin-profile",
    {
      method: "POST",

      body: JSON.stringify(
        profile
      ),
    }
  );
}


export async function updateSkinProfile(
  profile
) {

  return request(
    "/skin-profile",
    {
      method: "PUT",

      body: JSON.stringify(
        profile
      ),
    }
  );
}


// =========================================================
// SKIN IMAGE ANALYSIS
// =========================================================

export async function analyzeSkinImage(
  file
) {

  const formData =
    new FormData();

  formData.append(
    "file",
    file
  );


  return request(
    "/skin-analysis/upload",
    {
      method: "POST",
      body: formData,
    }
  );
}


// =========================================================
// INTELLIGENCE DASHBOARD
// =========================================================

export async function getDashboard() {

  return request(
    "/intelligence/dashboard"
  );
}


// =========================================================
// HEALTH SCORE
// =========================================================

export async function getHealthScore() {

  return request(
    "/intelligence/health-score"
  );
}


// =========================================================
// PERSONALIZED ROUTINE
// =========================================================

export async function getRoutine() {

  return request(
    "/intelligence/routine"
  );
}


// =========================================================
// INGREDIENT INTELLIGENCE
// =========================================================

export async function getIngredients() {

  return request(
    "/intelligence/ingredients"
  );
}


export async function analyzeIngredient(
  ingredient
) {

  return request(
    "/intelligence/ingredients/analyze",
    {
      method: "POST",

      body: JSON.stringify({
        ingredient,
      }),
    }
  );
}


// =========================================================
// PRODUCT RECOMMENDATIONS
// =========================================================

export async function getRecommendedProducts() {

  return request(
    "/intelligence/products/recommend"
  );
}


// =========================================================
// PROGRESS TRACKING
// =========================================================

export async function getProgress() {

  return request(
    "/intelligence/progress"
  );
}


// =========================================================
// GENERAL RECOMMENDATIONS
// =========================================================

export async function getRecommendations() {

  return request(
    "/intelligence/recommendations"
  );
}


// =========================================================
// BACKEND HEALTH
// =========================================================

export async function checkBackend() {

  return request(
    "/"
  );
}