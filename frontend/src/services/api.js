// ============================================================
// SKIN INTELLIGENCE
// FRONTEND API SERVICE
// ============================================================
//
// This file handles communication between the React frontend
// and the FastAPI backend.
//
// Backend:
// http://127.0.0.1:8000
//
// Frontend:
// http://localhost:5173
//
// ============================================================


// ============================================================
// API BASE URL
// ============================================================

const API_BASE_URL =
  import.meta.env.VITE_API_URL ||
  "http://127.0.0.1:8000";


// ============================================================
// TOKEN HELPER
// ============================================================

function getToken() {
  return localStorage.getItem(
    "skin_intelligence_token"
  );
}


// ============================================================
// MAIN REQUEST HELPER
// ============================================================

async function request(
  endpoint,
  options = {}
) {

  const token = getToken();

  const isFormData =
    options.body instanceof FormData;

  const headers = {
    ...(options.headers || {}),
  };


  // ----------------------------------------------------------
  // JSON CONTENT TYPE
  // ----------------------------------------------------------

  if (!isFormData) {

    headers["Content-Type"] =
      "application/json";

  }


  // ----------------------------------------------------------
  // JWT AUTHENTICATION
  // ----------------------------------------------------------

  if (token) {

    headers.Authorization =
      `Bearer ${token}`;

  }


  // ----------------------------------------------------------
  // SEND REQUEST
  // ----------------------------------------------------------

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

    const networkError =
      new Error(
        "Unable to connect to the backend. Make sure FastAPI is running on port 8000."
      );

    networkError.status = 0;

    throw networkError;

  }


  // ----------------------------------------------------------
  // READ RESPONSE
  // ----------------------------------------------------------

  const contentType =
    response.headers.get(
      "content-type"
    ) || "";

  let data;

  try {

    if (
      contentType.includes(
        "application/json"
      )
    ) {

      data =
        await response.json();

    } else {

      data =
        await response.text();

    }

  } catch {

    data = null;

  }


  // ----------------------------------------------------------
  // HANDLE HTTP ERRORS
  // ----------------------------------------------------------

  if (!response.ok) {

    let message =
      `Request failed with status ${response.status}.`;


    if (
      data &&
      typeof data === "object"
    ) {

      if (
        typeof data.detail ===
        "string"
      ) {

        message = data.detail;

      } else if (
        Array.isArray(data.detail)
      ) {

        message =
          data.detail
            .map(
              (item) =>
                item?.msg ||
                String(item)
            )
            .join(", ");

      } else if (
        typeof data.message ===
        "string"
      ) {

        message = data.message;

      }

    } else if (
      typeof data === "string" &&
      data.trim()
    ) {

      message = data;

    }


    const error =
      new Error(message);

    error.status =
      response.status;

    error.data = data;

    throw error;

  }


  return data;

}


// ============================================================
// AUTHENTICATION
// ============================================================


// ------------------------------------------------------------
// LOGIN
// ------------------------------------------------------------

export async function login(
  email,
  password
) {

  return request(
    "/auth/login",
    {
      method: "POST",

      body: JSON.stringify({
        email,
        password,
      }),
    }
  );

}


// ------------------------------------------------------------
// REGISTER
// ------------------------------------------------------------

export async function register(
  userData
) {

  return request(
    "/auth/register",
    {
      method: "POST",

      body: JSON.stringify({
        name:
          userData?.name || "",

        email:
          userData?.email || "",

        password:
          userData?.password || "",

        age:
          userData?.age ??
          null,

        gender:
          userData?.gender ||
          null,
      }),
    }
  );

}


// ------------------------------------------------------------
// CURRENT USER
// ------------------------------------------------------------
//
// This endpoint is ONLY for account information.
// It is NOT used for Skin Profile information.
//
// ------------------------------------------------------------

export async function getMe() {

  return request(
    "/auth/me",
    {
      method: "GET",
    }
  );

}


// ============================================================
// SKIN PROFILE
// ============================================================
//
// IMPORTANT:
//
// /auth/me
//      ↓
// User account information
//
// /skin-profile
//      ↓
// Skin information
//
// This separation allows every user to have their own
// independent skin profile.
//
// ============================================================


// ------------------------------------------------------------
// GET SKIN PROFILE
// ------------------------------------------------------------

export async function getSkinProfile() {

  return request(
    "/skin-profile",
    {
      method: "GET",
    }
  );

}


// ------------------------------------------------------------
// CREATE SKIN PROFILE
// ------------------------------------------------------------

export async function createSkinProfile(
  profile
) {

  return request(
    "/skin-profile",
    {
      method: "POST",

      body: JSON.stringify({

        skin_type:
          profile?.skin_type ||
          null,

        age_group:
          profile?.age_group ||
          null,

        concerns:
          profile?.concerns ||
          null,

        allergies:
          profile?.allergies ||
          null,

        sensitivities:
          profile?.sensitivities ||
          null,

        lifestyle:
          profile?.lifestyle ||
          null,

        sleep_quality:
          profile?.sleep_quality ||
          null,

        water_intake:
          profile?.water_intake ===
          ""
            ? null
            : profile?.water_intake ??
              null,

        environmental_exposure:
          profile?.environmental_exposure ||
          null,

        additional_notes:
          profile?.additional_notes ||
          null,

      }),
    }
  );

}


// ------------------------------------------------------------
// UPDATE SKIN PROFILE
// ------------------------------------------------------------

export async function updateSkinProfile(
  profile
) {

  return request(
    "/skin-profile",
    {
      method: "PUT",

      body: JSON.stringify({

        skin_type:
          profile?.skin_type ||
          null,

        age_group:
          profile?.age_group ||
          null,

        concerns:
          profile?.concerns ||
          null,

        allergies:
          profile?.allergies ||
          null,

        sensitivities:
          profile?.sensitivities ||
          null,

        lifestyle:
          profile?.lifestyle ||
          null,

        sleep_quality:
          profile?.sleep_quality ||
          null,

        water_intake:
          profile?.water_intake ===
          ""
            ? null
            : profile?.water_intake ??
              null,

        environmental_exposure:
          profile?.environmental_exposure ||
          null,

        additional_notes:
          profile?.additional_notes ||
          null,

      }),
    }
  );

}


// ============================================================
// AI SKIN ANALYSIS
// ============================================================


// ------------------------------------------------------------
// ANALYZE SKIN IMAGE
// ------------------------------------------------------------

export async function analyzeSkinImage(
  file
) {

  if (!file) {

    throw new Error(
      "Please select a skin image first."
    );

  }


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


// ============================================================
// INTELLIGENCE DASHBOARD
// ============================================================


// ------------------------------------------------------------
// DASHBOARD
// ------------------------------------------------------------

export async function getDashboard() {

  return request(
    "/intelligence/dashboard",
    {
      method: "GET",
    }
  );

}


// ============================================================
// HEALTH SCORE
// ============================================================


// ------------------------------------------------------------
// PERSONALIZED HEALTH SCORE
// ------------------------------------------------------------

export async function getHealthScore() {

  return request(
    "/intelligence/health-score",
    {
      method: "GET",
    }
  );

}


// ============================================================
// PERSONALIZED ROUTINE
// ============================================================


// ------------------------------------------------------------
// ROUTINE
// ------------------------------------------------------------

export async function getRoutine() {

  return request(
    "/intelligence/routine",
    {
      method: "GET",
    }
  );

}


// ============================================================
// INGREDIENT INTELLIGENCE
// ============================================================


// ------------------------------------------------------------
// GET ALL INGREDIENTS
// ------------------------------------------------------------

export async function getIngredients() {

  return request(
    "/intelligence/ingredients",
    {
      method: "GET",
    }
  );

}


// ------------------------------------------------------------
// ANALYZE INGREDIENT
// ------------------------------------------------------------

export async function analyzeIngredient(
  ingredient
) {

  return request(
    "/intelligence/ingredients/analyze",
    {
      method: "POST",

      body: JSON.stringify({

        ingredient:
          ingredient,

      }),
    }
  );

}


// ============================================================
// PRODUCT RECOMMENDATIONS
// ============================================================


// ------------------------------------------------------------
// GET RECOMMENDED PRODUCTS
// ------------------------------------------------------------

export async function getRecommendedProducts() {

  return request(
    "/intelligence/products/recommend",
    {
      method: "GET",
    }
  );

}


// ============================================================
// PROGRESS
// ============================================================


// ------------------------------------------------------------
// GET PROGRESS
// ------------------------------------------------------------

export async function getProgress() {

  return request(
    "/intelligence/progress",
    {
      method: "GET",
    }
  );

}


// ============================================================
// RECOMMENDATIONS
// ============================================================


// ------------------------------------------------------------
// GET PERSONALIZED RECOMMENDATIONS
// ------------------------------------------------------------

export async function getRecommendations() {

  return request(
    "/intelligence/recommendations",
    {
      method: "GET",
    }
  );

}


// ============================================================
// BACKEND CONNECTION CHECK
// ============================================================


// ------------------------------------------------------------
// CHECK BACKEND
// ------------------------------------------------------------

export async function checkBackend() {

  return request(
    "/",
    {
      method: "GET",
    }
  );

}


// ============================================================
// OPTIONAL GENERIC HELPERS
// ============================================================
//
// These are kept here so future modules can use the same
// request system without creating duplicate fetch logic.
//
// ============================================================


// ------------------------------------------------------------
// GENERIC GET
// ------------------------------------------------------------

export async function apiGet(
  endpoint
) {

  return request(
    endpoint,
    {
      method: "GET",
    }
  );

}


// ------------------------------------------------------------
// GENERIC POST
// ------------------------------------------------------------

export async function apiPost(
  endpoint,
  data
) {

  return request(
    endpoint,
    {
      method: "POST",

      body:
        data instanceof FormData
          ? data
          : JSON.stringify(data),
    }
  );

}


// ------------------------------------------------------------
// GENERIC PUT
// ------------------------------------------------------------

export async function apiPut(
  endpoint,
  data
) {

  return request(
    endpoint,
    {
      method: "PUT",

      body:
        data instanceof FormData
          ? data
          : JSON.stringify(data),
    }
  );

}


// ------------------------------------------------------------
// GENERIC DELETE
// ------------------------------------------------------------

export async function apiDelete(
  endpoint
) {

  return request(
    endpoint,
    {
      method: "DELETE",
    }
  );

}


// ============================================================
// EXPORT API BASE URL
// ============================================================

export {
  API_BASE_URL,
};