import React, { useEffect, useMemo, useState } from "react";

import {
  login,
  register,
  getMe,
  getSkinProfile,
  createSkinProfile,
  updateSkinProfile,
  analyzeSkinImage,
  getDashboard,
  getHealthScore,
  getRoutine,
  getIngredients,
  analyzeIngredient,
  getRecommendedProducts,
  getProgress,
  getRecommendations,
  checkBackend,
} from "./services/api";

import {
  saveToken,
  saveUser,
  getToken,
  getSavedUser,
  clearAuth,
} from "./auth";

import "./App.css";

const NAV_ITEMS = [
  {
    id: "dashboard",
    label: "Dashboard",
    icon: "⌂",
  },
  {
    id: "profile",
    label: "Skin Profile",
    icon: "◉",
  },
  {
    id: "analysis",
    label: "AI Skin Analysis",
    icon: "✦",
  },
  {
    id: "routine",
    label: "My Routine",
    icon: "✓",
  },
  {
    id: "ingredients",
    label: "Ingredients",
    icon: "◈",
  },
  {
    id: "products",
    label: "Products",
    icon: "▣",
  },
  {
    id: "progress",
    label: "Progress",
    icon: "↗",
  },
  {
    id: "reports",
    label: "Reports",
    icon: "▤",
  },
  {
    id: "notifications",
    label: "Notifications",
    icon: "♢",
  },
];


const DEFAULT_PROFILE = {
  skin_type: "",
  age_group: "",
  concerns: "",
  allergies: "",
  sensitivities: "",
  lifestyle: "",
  sleep_quality: "",
  water_intake: "",
  environmental_exposure: "",
};


function normalizeArray(value) {
  if (Array.isArray(value)) return value;

  if (typeof value === "string") {
    return value
      .split(",")
      .map((item) => item.trim())
      .filter(Boolean);
  }

  return [];
}


function getNumber(value, fallback = 0) {
  const number = Number(value);

  return Number.isFinite(number)
    ? number
    : fallback;
}


function extractScore(data) {
  if (!data) return 0;

  return getNumber(
    data.score ??
    data.health_score ??
    data.skin_health_score ??
    data.overall_score ??
    data.overall_health_score,
    0
  );
}


function getConditionLabel(score) {
  if (score >= 80) return "Excellent";
  if (score >= 65) return "Good";
  if (score >= 50) return "Fair";

  return "Needs Attention";
}


function App() {
  const [authenticated, setAuthenticated] = useState(
    Boolean(getToken())
  );

  const [user, setUser] = useState(
    getSavedUser()
  );

  const [activePage, setActivePage] = useState(
    "dashboard"
  );

  const [mobileMenu, setMobileMenu] =
    useState(false);

  const [loading, setLoading] =
    useState(Boolean(getToken()));

  const [backendOnline, setBackendOnline] =
    useState(false);

  const [globalError, setGlobalError] =
    useState("");


  /* =========================================================
     APP DATA
  ========================================================= */

  const [dashboard, setDashboard] =
    useState(null);

  const [healthScore, setHealthScore] =
    useState(null);

  const [routine, setRoutine] =
    useState(null);

  const [ingredients, setIngredients] =
    useState([]);

  const [products, setProducts] =
    useState([]);

  const [progress, setProgress] =
    useState(null);

  const [recommendations, setRecommendations] =
    useState([]);


  /* =========================================================
     LOGIN / REGISTER
  ========================================================= */

  const [authMode, setAuthMode] =
    useState("login");

  const [authLoading, setAuthLoading] =
    useState(false);

  const [authError, setAuthError] =
    useState("");

  const [authForm, setAuthForm] =
    useState({
      name: "",
      email: "",
      password: "",
      age: "",
      gender: "",
    });


  /* =========================================================
     PROFILE
  ========================================================= */

  const [profile, setProfile] =
    useState(DEFAULT_PROFILE);

  const [profileLoading, setProfileLoading] =
    useState(false);

  const [profileMessage, setProfileMessage] =
    useState("");


  /* =========================================================
     IMAGE ANALYSIS
  ========================================================= */

  const [selectedImage, setSelectedImage] =
    useState(null);

  const [imagePreview, setImagePreview] =
    useState("");

  const [analysis, setAnalysis] =
    useState(null);

  const [analysisLoading, setAnalysisLoading] =
    useState(false);


  /* =========================================================
     INGREDIENT
  ========================================================= */

  const [ingredientInput, setIngredientInput] =
    useState("");

  const [ingredientResult, setIngredientResult] =
    useState(null);

  const [ingredientLoading, setIngredientLoading] =
    useState(false);


  /* =========================================================
     ROUTINE CHECKLIST
  ========================================================= */

  const [completedRoutine, setCompletedRoutine] =
    useState(() => {
      try {
        return JSON.parse(
          localStorage.getItem(
            "skin_routine_completed"
          )
        ) || {};
      } catch {
        return {};
      }
    });


  /* =========================================================
     BACKEND CHECK
  ========================================================= */

  useEffect(() => {
    checkBackend()
      .then(() => setBackendOnline(true))
      .catch(() => setBackendOnline(false));
  }, []);


  /* =========================================================
     RESTORE SESSION
  ========================================================= */

  useEffect(() => {
    if (!getToken()) {
      setLoading(false);
      return;
    }

    restoreSession();
  }, []);


  async function restoreSession() {
    try {
      const currentUser = await getMe();

      setUser(currentUser);
      saveUser(currentUser);
      setAuthenticated(true);

      await loadApplicationData();
    } catch (error) {
      clearAuth();

      setAuthenticated(false);
      setUser(null);

      if (error.status !== 401) {
        setGlobalError(
          error.message ||
          "Unable to restore your session."
        );
      }
    } finally {
      setLoading(false);
    }
  }


  /* =========================================================
     LOAD DATA
  ========================================================= */

  async function loadApplicationData() {
    setGlobalError("");

    const results = await Promise.allSettled([
      getDashboard(),
      getHealthScore(),
      getRoutine(),
      getIngredients(),
      getRecommendedProducts(),
      getProgress(),
      getRecommendations(),
      getSkinProfile(),
    ]);

    const [
      dashboardResult,
      scoreResult,
      routineResult,
      ingredientsResult,
      productsResult,
      progressResult,
      recommendationsResult,
      profileResult,
    ] = results;


    if (dashboardResult.status === "fulfilled") {
      setDashboard(
        dashboardResult.value
      );
    }

    if (scoreResult.status === "fulfilled") {
      setHealthScore(
        scoreResult.value
      );
    }

    if (routineResult.status === "fulfilled") {
      setRoutine(
        routineResult.value
      );
    }

    if (ingredientsResult.status === "fulfilled") {
      const value =
        ingredientsResult.value;

      setIngredients(
        Array.isArray(value)
          ? value
          : value?.ingredients || []
      );
    }

    if (productsResult.status === "fulfilled") {
      const value =
        productsResult.value;

      setProducts(
        Array.isArray(value)
          ? value
          : value?.recommendations || []
      );
    }

    if (progressResult.status === "fulfilled") {
      setProgress(
        progressResult.value
      );
    }

    if (
      recommendationsResult.status ===
      "fulfilled"
    ) {
      const value =
        recommendationsResult.value;

      setRecommendations(
        Array.isArray(value)
          ? value
          : value?.recommendations || []
      );
    }

    if (profileResult.status === "fulfilled") {
      setProfile({
        ...DEFAULT_PROFILE,
        ...profileResult.value,
      });
    }
  }


  /* =========================================================
     AUTH SUBMIT
  ========================================================= */

  async function handleAuthSubmit(event) {
    event.preventDefault();

    setAuthError("");
    setAuthLoading(true);

    try {
      if (authMode === "register") {
        await register({
          name: authForm.name,
          email: authForm.email,
          password: authForm.password,
          age: authForm.age
            ? Number(authForm.age)
            : null,
          gender:
            authForm.gender || null,
        });

        setAuthMode("login");

        setAuthForm({
          ...authForm,
          password: "",
        });

        setAuthError(
          "Registration successful. Please log in."
        );

        return;
      }


      const response = await login(
        authForm.email,
        authForm.password
      );

      if (!response?.access_token) {
        throw new Error(
          "Login succeeded but no access token was returned."
        );
      }

      saveToken(response.access_token);

      const savedUser = {
        user_id: response.user_id,
        name: response.name,
        email: response.email,
      };

      saveUser(savedUser);

      setUser(savedUser);
      setAuthenticated(true);

      setAuthForm({
        name: "",
        email: "",
        password: "",
        age: "",
        gender: "",
      });

      await restoreSession();

    } catch (error) {
      setAuthError(
        error.message ||
        "Unable to authenticate."
      );
    } finally {
      setAuthLoading(false);
    }
  }


  function handleLogout() {
    clearAuth();

    setAuthenticated(false);
    setUser(null);

    setDashboard(null);
    setHealthScore(null);
    setRoutine(null);
    setProducts([]);
    setIngredients([]);
    setProgress(null);

    setActivePage("dashboard");
  }


  /* =========================================================
     PROFILE
  ========================================================= */

  function updateProfileField(
    field,
    value
  ) {
    setProfile((previous) => ({
      ...previous,
      [field]: value,
    }));
  }


  async function handleSaveProfile(event) {
    event.preventDefault();

    setProfileLoading(true);
    setProfileMessage("");

    try {
      let response;

      if (profile.id) {
        response =
          await updateSkinProfile(profile);
      } else {
        response =
          await createSkinProfile(profile);
      }

      setProfile({
        ...profile,
        ...response,
      });

      setProfileMessage(
        "Your skin profile has been saved successfully."
      );

      await loadApplicationData();

    } catch (error) {
      setProfileMessage(
        error.message ||
        "Unable to save your profile."
      );
    } finally {
      setProfileLoading(false);
    }
  }


  /* =========================================================
     IMAGE ANALYSIS
  ========================================================= */

  function handleImageChange(event) {
    const file =
      event.target.files?.[0];

    if (!file) return;

    setSelectedImage(file);
    setAnalysis(null);

    const url =
      URL.createObjectURL(file);

    setImagePreview(url);
  }


  async function handleAnalysis() {
    if (!selectedImage) {
      return;
    }

    setAnalysisLoading(true);
    setGlobalError("");

    try {
      const result =
        await analyzeSkinImage(
          selectedImage
        );

      setAnalysis(result);

      await loadApplicationData();

    } catch (error) {
      setGlobalError(
        error.message ||
        "Skin analysis failed."
      );
    } finally {
      setAnalysisLoading(false);
    }
  }


  /* =========================================================
     INGREDIENT ANALYSIS
  ========================================================= */

  async function handleIngredientAnalysis(
    event
  ) {
    event.preventDefault();

    if (!ingredientInput.trim()) {
      return;
    }

    setIngredientLoading(true);
    setIngredientResult(null);

    try {
      const result =
        await analyzeIngredient(
          ingredientInput.trim()
        );

      setIngredientResult(result);

    } catch (error) {
      setIngredientResult({
        error:
          error.message ||
          "Ingredient analysis failed.",
      });
    } finally {
      setIngredientLoading(false);
    }
  }


  /* =========================================================
     ROUTINE
  ========================================================= */

  function toggleRoutineItem(id) {
    setCompletedRoutine(
      (previous) => {
        const updated = {
          ...previous,
          [id]: !previous[id],
        };

        localStorage.setItem(
          "skin_routine_completed",
          JSON.stringify(updated)
        );

        return updated;
      }
    );
  }


  /* =========================================================
     SCORE
  ========================================================= */

  const score =
    extractScore(
      healthScore || dashboard
    );

  const scoreLabel =
    getConditionLabel(score);


  const routineItems =
    useMemo(() => {
      if (!routine) return [];

      const morning =
        routine.morning ||
        routine.morning_routine ||
        [];

      const evening =
        routine.evening ||
        routine.evening_routine ||
        [];

      const weekly =
        routine.weekly ||
        routine.weekly_treatment ||
        [];

      const convert = (items, period) =>
  normalizeArray(items).map((item, index) => {
    let name =
      typeof item === "object"
        ? item.name || item.title || ""
        : item;

    // Replace backend placeholder names
    if (
      !name ||
      name.toLowerCase() === "skincare step"
    ) {
      const fallbackSteps = {
        Morning: [
          "Gentle Cleanser",
          "Treatment Serum",
          "Moisturizer",
          "Sunscreen",
        ],
        Evening: [
          "Gentle Cleanser",
          "Treatment",
          "Moisturizer",
        ],
        Weekly: [
          "Exfoliation",
          "Hydrating Treatment",
        ],
      };

      name =
        fallbackSteps[period]?.[index] ||
        "Skincare Step";
    }

    return {
      id: `${period}-${index}-${name}`,
      name,
      period,
    };
  });

      return [
        ...convert(morning, "Morning"),
        ...convert(evening, "Evening"),
        ...convert(weekly, "Weekly"),
      ];
    }, [routine]);


  /* =========================================================
     AUTH SCREEN
  ========================================================= */

  if (!authenticated) {
    return (
      <AuthScreen
        mode={authMode}
        setMode={setAuthMode}
        form={authForm}
        setForm={setAuthForm}
        error={authError}
        loading={authLoading}
        backendOnline={backendOnline}
        onSubmit={handleAuthSubmit}
      />
    );
  }


  /* =========================================================
     MAIN APP
  ========================================================= */

  return (
    <div className="app-shell">

      {mobileMenu && (
        <div
          className="mobile-overlay"
          onClick={() =>
            setMobileMenu(false)
          }
        />
      )}


      <aside
        className={`sidebar ${
          mobileMenu
            ? "sidebar-open"
            : ""
        }`}
      >

        <div className="brand">
          <div className="brand-mark">
            ✦
          </div>

          <div>
            <h1>
              Skin Intelligence
            </h1>

            <span>
              Personalized Skincare
            </span>
          </div>
        </div>


        <div className="sidebar-section-title">
          MAIN MENU
        </div>


        <nav className="sidebar-nav">

          {NAV_ITEMS.map((item) => (
            <button
              key={item.id}
              className={`nav-item ${
                activePage === item.id
                  ? "active"
                  : ""
              }`}
              onClick={() => {
                setActivePage(item.id);
                setMobileMenu(false);
              }}
            >
              <span className="nav-icon">
                {item.icon}
              </span>

              <span>
                {item.label}
              </span>
            </button>
          ))}

        </nav>


        <div className="sidebar-bottom">

          <div className="backend-status">

            <span
              className={
                backendOnline
                  ? "status-dot online"
                  : "status-dot offline"
              }
            />

            <span>
              {backendOnline
                ? "Backend connected"
                : "Backend offline"}
            </span>

          </div>


          <button
            className="logout-button"
            onClick={handleLogout}
          >
            <span>↪</span>
            Logout
          </button>

        </div>

      </aside>


      <main className="main-area">

        <header className="topbar">

          <button
            className="mobile-menu-button"
            onClick={() =>
              setMobileMenu(true)
            }
          >
            ☰
          </button>


          <div className="topbar-title">

            <span>
              {NAV_ITEMS.find(
                (item) =>
                  item.id === activePage
              )?.label}
            </span>

            <small>
              AI-assisted skin intelligence
            </small>

          </div>


          <div className="topbar-right">

            <button className="notification-button">
              ♢
              <span />
            </button>


            <div className="user-chip">

              <div className="avatar">
                {(user?.name || "U")
                  .charAt(0)
                  .toUpperCase()}
              </div>

              <div>
                <strong>
                  {user?.name ||
                    "User"}
                </strong>

                <small>
                  {user?.email || ""}
                </small>
              </div>

            </div>

          </div>

        </header>


        <div className="content">

          {globalError && (
            <div className="global-error">
              <strong>
                Something went wrong
              </strong>

              <span>
                {globalError}
              </span>

              <button
                onClick={() =>
                  setGlobalError("")
                }
              >
                ×
              </button>
            </div>
          )}


          {loading ? (
            <LoadingScreen />
          ) : (
            <>
              {activePage === "dashboard" && (
                <DashboardPage
                  user={user}
                  score={score}
                  scoreLabel={scoreLabel}
                  profile={profile}
                  routineItems={routineItems}
                  completedRoutine={
                    completedRoutine
                  }
                  toggleRoutineItem={
                    toggleRoutineItem
                  }
                  analysis={analysis}
                  setActivePage={
                    setActivePage
                  }
                  recommendations={
                    recommendations
                  }
                  products={products}
                  dashboard={dashboard}
                />
              )}


              {activePage === "profile" && (
                <ProfilePage
                  profile={profile}
                  updateProfileField={
                    updateProfileField
                  }
                  onSubmit={
                    handleSaveProfile
                  }
                  loading={
                    profileLoading
                  }
                  message={
                    profileMessage
                  }
                />
              )}


              {activePage === "analysis" && (
                <AnalysisPage
                  selectedImage={
                    selectedImage
                  }
                  imagePreview={
                    imagePreview
                  }
                  analysis={
                    analysis
                  }
                  loading={
                    analysisLoading
                  }
                  onImageChange={
                    handleImageChange
                  }
                  onAnalyze={
                    handleAnalysis
                  }
                />
              )}


              {activePage === "routine" && (
                <RoutinePage
                  routine={
                    routine
                  }
                  routineItems={
                    routineItems
                  }
                  completedRoutine={
                    completedRoutine
                  }
                  toggleRoutineItem={
                    toggleRoutineItem
                  }
                />
              )}


              {activePage === "ingredients" && (
                <IngredientsPage
                  ingredients={
                    ingredients
                  }
                  input={
                    ingredientInput
                  }
                  setInput={
                    setIngredientInput
                  }
                  result={
                    ingredientResult
                  }
                  loading={
                    ingredientLoading
                  }
                  onSubmit={
                    handleIngredientAnalysis
                  }
                />
              )}


              {activePage === "products" && (
                <ProductsPage
                  products={
                    products
                  }
                />
              )}


              {activePage === "progress" && (
                <ProgressPage
                  progress={progress}
                  routineItems={routineItems}
                  completedRoutine={completedRoutine}
                />
              )}


              {activePage === "reports" && (
                <ReportsPage
                  score={score}
                  profile={profile}
                  analysis={analysis}
                  routine={routine}
                  products={products}
                  progress={progress}
                />
              )}


              {activePage === "notifications" && (
                <NotificationsPage />
              )}

            </>
          )}

        </div>

      </main>

    </div>
  );
}


/* ============================================================
   AUTH SCREEN
============================================================ */

function AuthScreen({
  mode,
  setMode,
  form,
  setForm,
  error,
  loading,
  backendOnline,
  onSubmit,
}) {

  function update(
    field,
    value
  ) {
    setForm((previous) => ({
      ...previous,
      [field]: value,
    }));
  }


  return (
    <div className="auth-page">

      <div className="auth-decoration">
        <div />
        <div />
        <div />
      </div>


      <div className="auth-card">

        <div className="auth-brand">
          <div className="auth-logo">
            ✦
          </div>

          <h1>
            Skin Intelligence
          </h1>

          <p>
            AI-Assisted Personalized
            Skincare Platform
          </p>
        </div>


        <div className="auth-status">

          <span
            className={
              backendOnline
                ? "status-dot online"
                : "status-dot offline"
            }
          />

          {backendOnline
            ? "Backend connected"
            : "Backend not connected"}

        </div>


        <div className="auth-tabs">

          <button
            className={
              mode === "login"
                ? "active"
                : ""
            }
            onClick={() =>
              setMode("login")
            }
          >
            Login
          </button>

          <button
            className={
              mode === "register"
                ? "active"
                : ""
            }
            onClick={() =>
              setMode("register")
            }
          >
            Create Account
          </button>

        </div>


        <form
          className="auth-form"
          onSubmit={onSubmit}
        >

          {mode === "register" && (
            <>
              <label>
                Full Name

                <input
                  value={form.name}
                  onChange={(event) =>
                    update(
                      "name",
                      event.target.value
                    )
                  }
                  required
                />
              </label>


              <div className="form-row">

                <label>
                  Age

                  <input
                    type="number"
                    min="1"
                    max="120"
                    value={form.age}
                    onChange={(event) =>
                      update(
                        "age",
                        event.target.value
                      )
                    }
                  />
                </label>


                <label>
                  Gender

                  <select
                    value={form.gender}
                    onChange={(event) =>
                      update(
                        "gender",
                        event.target.value
                      )
                    }
                  >
                    <option value="">
                      Select
                    </option>

                    <option value="Female">
                      Female
                    </option>

                    <option value="Male">
                      Male
                    </option>

                    <option value="Other">
                      Other
                    </option>
                  </select>

                </label>

              </div>
            </>
          )}


          <label>
            Email Address

            <input
              type="email"
              value={form.email}
              onChange={(event) =>
                update(
                  "email",
                  event.target.value
                )
              }
              required
            />
          </label>


          <label>
            Password

            <input
              type="password"
              value={form.password}
              onChange={(event) =>
                update(
                  "password",
                  event.target.value
                )
              }
              required
              minLength="6"
            />
          </label>


          {error && (
            <div
              className={
                error.includes(
                  "successful"
                )
                  ? "auth-message success"
                  : "auth-message error"
              }
            >
              {error}
            </div>
          )}


          <button
            className="primary-button auth-submit"
            disabled={loading}
          >
            {loading
              ? "Please wait..."
              : mode === "login"
              ? "Sign In"
              : "Create Account"}
          </button>

        </form>


        <div className="auth-footer">
          Your skincare information is
          protected by authenticated API access.
        </div>

      </div>

    </div>
  );
}


/* ============================================================
   LOADING
============================================================ */

function LoadingScreen() {
  return (
    <div className="loading-screen">
      <div className="loading-spinner" />

      <h2>
        Loading your Skin Intelligence
      </h2>

      <p>
        Preparing your personalized
        skincare dashboard...
      </p>
    </div>
  );
}


/* ============================================================
   PAGE HEADER
============================================================ */

function PageHeader({
  eyebrow,
  title,
  description,
}) {
  return (
    <div className="page-header">

      <div>
        {eyebrow && (
          <span className="eyebrow">
            {eyebrow}
          </span>
        )}

        <h2>
          {title}
        </h2>

        {description && (
          <p>
            {description}
          </p>
        )}
      </div>

    </div>
  );
}


/* ============================================================
   DASHBOARD
============================================================ */

function DashboardPage({
  user,
  score,
  scoreLabel,
  profile,
  routineItems,
  completedRoutine,
  toggleRoutineItem,
  setActivePage,
  recommendations,
  products,
  analysis,
}) {

  const completed =
    routineItems.filter(
      (item) =>
        completedRoutine[item.id]
    ).length;

  const routinePercentage =
    routineItems.length
      ? Math.round(
          (completed /
            routineItems.length) *
            100
        )
      : 0;


  const concerns =
    normalizeArray(
      profile?.concerns
    );


  return (
    <div>

      <PageHeader
        eyebrow="YOUR OVERVIEW"
        title={`Good day, ${
          user?.name || "there"
        } 👋`}
        description="Your personalized skin health overview and recommendations."
      />


      <div className="dashboard-grid">

        <StatCard
          title="Skin Health"
          value={`${Math.round(
            score
          )}/100`}
          subtitle={scoreLabel}
          icon="♡"
          accent="green"
        />

        <StatCard
          title="Skin Type"
          value={
            profile?.skin_type ||
            "Not set"
          }
          subtitle="Current profile"
          icon="◉"
          accent="blue"
        />

        <StatCard
          title="Top Concern"
          value={
            concerns[0] ||
            "Not identified"
          }
          subtitle={
            concerns.length > 1
              ? `+ ${
                  concerns.length - 1
                } more`
              : "Your priority"
          }
          icon="!"
          accent="orange"
        />

        <StatCard
          title="Routine"
          value={`${routinePercentage}%`}
          subtitle="Completed today"
          icon="✓"
          accent="purple"
        />

      </div>


      <div className="dashboard-two-column">

        <section className="card health-card">

          <div className="card-header">

            <div>
              <span className="card-eyebrow">
                SKIN HEALTH
              </span>

              <h3>
                Your Health Score
              </h3>
            </div>

            <span className="soft-badge">
              {scoreLabel}
            </span>

          </div>


          <div className="score-area">

            <div
              className="score-ring"
              style={{
                "--score":
                  `${score}%`,
              }}
            >
              <div>
                <strong>
                  {Math.round(score)}
                </strong>

                <span>
                  /100
                </span>
              </div>
            </div>


            <div className="score-details">

              <p>
                Your score combines
                skin condition, lifestyle,
                sleep, routine consistency
                and hydration.
              </p>

              <button
                className="text-button"
                onClick={() =>
                  setActivePage(
                    "analysis"
                  )
                }
              >
                Run new AI assessment →
              </button>

            </div>

          </div>

        </section>


        <section className="card">

          <div className="card-header">

            <div>
              <span className="card-eyebrow">
                TODAY
              </span>

              <h3>
                Skincare Checklist
              </h3>
            </div>

            <button
              className="small-link"
              onClick={() =>
                setActivePage(
                  "routine"
                )
              }
            >
              View routine
            </button>

          </div>


          {routineItems.length === 0 ? (
            <EmptyState
              title="No routine yet"
              description="Complete your skin profile to generate a personalized routine."
            />
          ) : (
            <div className="checklist">

              {routineItems
                .slice(0, 5)
                .map((item) => {

                  const done =
                    completedRoutine[
                      item.id
                    ];

                  return (
                    <button
                      key={item.id}
                      className={`check-item ${
                        done
                          ? "completed"
                          : ""
                      }`}
                      onClick={() =>
                        toggleRoutineItem(
                          item.id
                        )
                      }
                    >

                      <span className="check-circle">
                        {done
                          ? "✓"
                          : ""}
                      </span>

                      <span className="check-content">
                        <strong>
                          {item.name}
                        </strong>

                        <small>
                          {item.period}
                        </small>
                      </span>

                    </button>
                  );
                })}

            </div>
          )}

        </section>

      </div>


      <div className="dashboard-two-column">

        <section className="card">

          <div className="card-header">

            <div>
              <span className="card-eyebrow">
                AI INSIGHTS
              </span>

              <h3>
                Latest Skin Analysis
              </h3>
            </div>

            <button
              className="small-link"
              onClick={() =>
                setActivePage(
                  "analysis"
                )
              }
            >
              Analyze image
            </button>

          </div>


          {analysis ? (
            <AnalysisSummary
              analysis={analysis}
            />
          ) : (
            <div className="analysis-placeholder">

              <div className="placeholder-icon">
                ✦
              </div>

              <div>
                <strong>
                  Get your AI skin assessment
                </strong>

                <p>
                  Upload a clear skin
                  image to identify
                  possible conditions
                  and confidence scores.
                </p>
              </div>

            </div>
          )}

        </section>


        <section className="card">

          <div className="card-header">

            <div>
              <span className="card-eyebrow">
                RECOMMENDATIONS
              </span>

              <h3>
                For You
              </h3>
            </div>

            <button
              className="small-link"
              onClick={() =>
                setActivePage(
                  "products"
                )
              }
            >
              View all
            </button>

          </div>


          <RecommendationList
            items={
              recommendations.length
                ? recommendations
                : products
            }
          />

        </section>

      </div>

    </div>
  );
}


/* ============================================================
   STAT CARD
============================================================ */

function StatCard({
  title,
  value,
  subtitle,
  icon,
  accent,
}) {
  return (
    <div
      className={`stat-card ${accent}`}
    >

      <div className="stat-top">

        <span>
          {title}
        </span>

        <div className="stat-icon">
          {icon}
        </div>

      </div>

      <strong>
        {value}
      </strong>

      <small>
        {subtitle}
      </small>

    </div>
  );
}


/* ============================================================
   PROFILE PAGE
============================================================ */

function ProfilePage({
  profile,
  updateProfileField,
  onSubmit,
  loading,
  message,
}) {

  return (
    <div>

      <PageHeader
        eyebrow="PERSONALIZATION"
        title="Your Skin Profile"
        description="Tell Skin Intelligence about your skin, lifestyle and environment so recommendations can be personalized."
      />


      <form
        className="card profile-form"
        onSubmit={onSubmit}
      >

        <div className="form-section">

          <div className="section-heading">
            <span>
              01
            </span>

            <div>
              <h3>
                Skin Information
              </h3>

              <p>
                Basic information about
                your skin.
              </p>
            </div>
          </div>


          <div className="form-grid">

            <FormField
              label="Skin Type"
              value={
                profile.skin_type
              }
              onChange={(value) =>
                updateProfileField(
                  "skin_type",
                  value
                )
              }
              type="select"
              options={[
                "Normal",
                "Dry",
                "Oily",
                "Combination",
                "Sensitive",
              ]}
            />


            <FormField
              label="Age Group"
              value={
                profile.age_group
              }
              onChange={(value) =>
                updateProfileField(
                  "age_group",
                  value
                )
              }
              type="select"
              options={[
                "Teen",
                "18-24",
                "25-34",
                "35-44",
                "45-54",
                "55+",
              ]}
            />


            <FormField
              label="Skin Concerns"
              value={
                profile.concerns
              }
              onChange={(value) =>
                updateProfileField(
                  "concerns",
                  value
                )
              }
              placeholder="Acne, dark spots, redness..."
            />


            <FormField
              label="Allergies"
              value={
                profile.allergies
              }
              onChange={(value) =>
                updateProfileField(
                  "allergies",
                  value
                )
              }
              placeholder="Ingredients or products"
            />


            <FormField
              label="Sensitivities"
              value={
                profile.sensitivities
              }
              onChange={(value) =>
                updateProfileField(
                  "sensitivities",
                  value
                )
              }
              placeholder="Fragrance, alcohol..."
            />

          </div>

        </div>


        <div className="form-section">

          <div className="section-heading">

            <span>
              02
            </span>

            <div>
              <h3>
                Lifestyle & Wellness
              </h3>

              <p>
                Lifestyle factors used
                by the health scoring
                engine.
              </p>
            </div>

          </div>


          <div className="form-grid">

            <FormField
              label="Lifestyle Habits"
              value={
                profile.lifestyle
              }
              onChange={(value) =>
                updateProfileField(
                  "lifestyle",
                  value
                )
              }
              placeholder="Exercise, stress, smoking..."
            />


            <FormField
              label="Sleep Quality"
              value={
                profile.sleep_quality
              }
              onChange={(value) =>
                updateProfileField(
                  "sleep_quality",
                  value
                )
              }
              type="select"
              options={[
                "Poor",
                "Fair",
                "Good",
                "Excellent",
              ]}
            />


            <FormField
              label="Water Intake"
              value={
                profile.water_intake
              }
              onChange={(value) =>
                updateProfileField(
                  "water_intake",
                  value
                )
              }
              placeholder="Example: 2 L/day"
            />


            <FormField
              label="Environmental Exposure"
              value={
                profile.environmental_exposure
              }
              onChange={(value) =>
                updateProfileField(
                  "environmental_exposure",
                  value
                )
              }
              placeholder="Sun, pollution, humidity..."
            />

          </div>

        </div>


        {message && (
          <div className="profile-message">
            {message}
          </div>
        )}


        <div className="form-actions">

          <button
            className="primary-button"
            disabled={loading}
          >
            {loading
              ? "Saving..."
              : "Save Skin Profile"}
          </button>

        </div>

      </form>

    </div>
  );
}


/* ============================================================
   FORM FIELD
============================================================ */

function FormField({
  label,
  value,
  onChange,
  type = "text",
  options = [],
  placeholder = "",
}) {

  return (
    <label className="form-field">

      <span>
        {label}
      </span>

      {type === "select" ? (
        <select
          value={value || ""}
          onChange={(event) =>
            onChange(
              event.target.value
            )
          }
        >
          <option value="">
            Select {label}
          </option>

          {options.map((option) => (
            <option
              key={option}
              value={option}
            >
              {option}
            </option>
          ))}

        </select>
      ) : (
        <input
          value={value || ""}
          onChange={(event) =>
            onChange(
              event.target.value
            )
          }
          placeholder={placeholder}
        />
      )}

    </label>
  );
}


/* ============================================================
   ANALYSIS PAGE
============================================================ */

function AnalysisPage({
  selectedImage,
  imagePreview,
  analysis,
  loading,
  onImageChange,
  onAnalyze,
}) {

  return (
    <div>

      <PageHeader
        eyebrow="AI / COMPUTER VISION"
        title="AI Skin Analysis"
        description="Upload a clear skin image and let the AI-assisted analysis engine evaluate possible skin conditions."
      />


      <div className="analysis-grid">

        <section className="card upload-card">

          <div className="upload-area">

            {imagePreview ? (
              <img
                src={imagePreview}
                className="skin-preview"
                alt="Selected skin"
              />
            ) : (
              <div className="upload-placeholder">

                <div className="upload-icon">
                  ↑
                </div>

                <h3>
                  Upload skin image
                </h3>

                <p>
                  Use a clear, well-lit
                  image for better
                  AI-assisted analysis.
                </p>

              </div>
            )}


            <label className="upload-button">

              Choose Image

              <input
                type="file"
                accept="image/*"
                onChange={
                  onImageChange
                }
              />

            </label>


            {selectedImage && (
              <p className="file-name">
                {selectedImage.name}
              </p>
            )}

          </div>


          <button
            className="primary-button full-width"
            disabled={
              !selectedImage ||
              loading
            }
            onClick={onAnalyze}
          >
            {loading
              ? "Analyzing skin..."
              : "Run AI Skin Analysis"}
          </button>

        </section>


        <section className="card results-card">

          <div className="card-header">

            <div>
              <span className="card-eyebrow">
                RESULTS
              </span>

              <h3>
                Analysis Result
              </h3>
            </div>

          </div>


          {!analysis ? (
            <EmptyState
              title="No analysis yet"
              description="Your AI assessment results will appear here after uploading an image."
            />
          ) : (
            <AnalysisSummary
              analysis={analysis}
              detailed
            />
          )}

        </section>

      </div>

    </div>
  );
}


/* ============================================================
   ANALYSIS SUMMARY
============================================================ */

function AnalysisSummary({
  analysis,
  detailed = false,
}) {
  // Backend returns the actual AI result inside "ai_analysis"
  const aiAnalysis =
    analysis?.ai_analysis || analysis || {};

  // Backend structure:
  // ai_analysis.top_prediction.label
  // ai_analysis.top_prediction.confidence
  // ai_analysis.top_prediction.confidence_percent

  const topPrediction =
    aiAnalysis?.top_prediction || {};

  const condition =
    topPrediction?.label ||
    aiAnalysis?.condition ||
    aiAnalysis?.predicted_condition ||
    aiAnalysis?.prediction ||
    aiAnalysis?.diagnosis ||
    "Unknown";

  const confidencePercent = getNumber(
    topPrediction?.confidence_percent ??
      aiAnalysis?.confidence_percent,
    0
  );

  const confidence =
    confidencePercent > 0
      ? confidencePercent
      : getNumber(
          topPrediction?.confidence ??
            aiAnalysis?.confidence ??
            aiAnalysis?.confidence_score ??
            aiAnalysis?.probability,
          0
        );

  const finalConfidence =
    confidence > 1
      ? confidence
      : confidence * 100;

  const predictions =
    aiAnalysis?.predictions ||
    aiAnalysis?.all_predictions ||
    [];

  return (
    <div className="analysis-result">

      {/* MAIN RESULT */}
      <div className="primary-result">

        <span>
          DETECTED CONDITION
        </span>

        <strong>
          {condition}
        </strong>

        {finalConfidence > 0 && (
          <div className="confidence">

            <div className="confidence-label">
              <span>
                Confidence
              </span>

              <strong>
                {finalConfidence.toFixed(2)}%
              </strong>
            </div>

            <div className="progress-track">
              <div
                className="progress-fill"
                style={{
                  width: `${Math.min(
                    finalConfidence,
                    100
                  )}%`,
                }}
              />
            </div>

          </div>
        )}

      </div>

      {/* ALL PREDICTIONS */}
      {detailed &&
        predictions.length > 0 && (
          <div className="prediction-list">

            <h4>
              All Predictions
            </h4>

            {predictions.map(
              (prediction, index) => {

                const name =
                  prediction?.label ||
                  prediction?.condition ||
                  prediction?.name ||
                  `Prediction ${index + 1}`;

                const rawConfidence =
                  prediction?.confidence_percent ??
                  prediction?.confidence ??
                  prediction?.score ??
                  prediction?.probability ??
                  0;

                const percentage =
                  rawConfidence > 1
                    ? rawConfidence
                    : rawConfidence * 100;

                return (
                  <div
                    className="prediction-row"
                    key={index}
                  >

                    <div>
                      <span>
                        {name}
                      </span>

                      <strong>
                        {percentage.toFixed(2)}%
                      </strong>
                    </div>

                    <div className="progress-track">
                      <div
                        className="progress-fill"
                        style={{
                          width: `${Math.min(
                            percentage,
                            100
                          )}%`,
                        }}
                      />
                    </div>

                  </div>
                );
              }
            )}

          </div>
        )}

      {/* MEDICAL DISCLAIMER */}
      <div className="medical-note">
        <strong>
          Important:
        </strong>

        AI analysis is for
        informational purposes and
        should not replace evaluation
        by a qualified dermatologist.
      </div>

    </div>
  );
}


/* ============================================================
   ROUTINE PAGE
============================================================ */

function RoutinePage({
  routine,
  routineItems,
  completedRoutine,
  toggleRoutineItem,
}) {

  const totalSteps = routineItems.length;

  const completedSteps = routineItems.filter(
    (item) => completedRoutine[item.id]
  ).length;

  const completionPercentage =
    totalSteps > 0
      ? Math.round((completedSteps / totalSteps) * 100)
      : 0;

  return (
    <div>

      <PageHeader
        eyebrow="PERSONALIZED CARE"
        title="My Skincare Routine"
        description="Your routine is generated from your skin profile, concerns and lifestyle information."
      />

      <section className="card routine-progress">
        <div className="routine-progress-header">
          <div>
            <span>ROUTINE PROGRESS</span>
            <h3>{completionPercentage}% Complete</h3>
          </div>

          <strong>
            {completedSteps}/{totalSteps}
          </strong>
        </div>

        <div className="routine-progress-bar">
          <div
            className="routine-progress-fill"
            style={{
              width: `${completionPercentage}%`,
            }}
          />
        </div>
      </section>


      <div className="routine-layout">

        {[
          "Morning",
          "Evening",
          "Weekly",
        ].map((period) => {

          const items =
            routineItems.filter(
              (item) =>
                item.period ===
                period
            );

          return (
            <section
              className="card routine-card"
              key={period}
            >

              <div className="routine-heading">

                <div className="routine-number">
                  {period === "Morning"
                    ? "☀"
                    : period === "Evening"
                    ? "☾"
                    : "◆"}
                </div>

                <div>
                  <span>
                    ROUTINE
                  </span>

                  <h3>
                    {period}
                  </h3>
                </div>

              </div>


              {items.length === 0 ? (
                <EmptyState
                  title={`No ${period.toLowerCase()} steps`}
                  description="Your personalized routine will appear here."
                />
              ) : (
                <div className="routine-list">

                  {items.map((item, index) => {

                    const done =
                      completedRoutine[
                        item.id
                      ];

                    return (
                      <button
                        className={`routine-item ${
                          done
                            ? "completed"
                            : ""
                        }`}
                        key={item.id}
                        onClick={() =>
                          toggleRoutineItem(
                            item.id
                          )
                        }
                      >

                        <span className="routine-step">
                          {index + 1}
                        </span>

                        <div>
                          <strong>
                            {item.name}
                          </strong>

                          <small>
                            {done
                              ? "Completed"
                              : "Tap to mark complete"}
                          </small>
                        </div>

                        <span className="routine-check">
                          {done
                            ? "✓"
                            : "○"}
                        </span>

                      </button>
                    );
                  })}

                </div>
              )}

            </section>
          );
        })}

      </div>

    </div>
  );
}


/* ============================================================
   INGREDIENTS
============================================================ */

function IngredientsPage({
  ingredients,
  input,
  setInput,
  result,
  loading,
  onSubmit,
}) {

  return (
    <div>

      <PageHeader
        eyebrow="INGREDIENT INTELLIGENCE"
        title="Understand Your Ingredients"
        description="Analyze ingredient suitability, potential interactions and allergy concerns."
      />


      <section className="card ingredient-search">

        <form
          onSubmit={onSubmit}
        >

          <label>
            Ingredient name

            <div className="search-input">

              <input
                value={input}
                onChange={(event) =>
                  setInput(
                    event.target.value
                  )
                }
                placeholder="Example: Niacinamide"
              />

              <button
                className="primary-button"
                disabled={loading}
              >
                {loading
                  ? "Analyzing..."
                  : "Analyze"}
              </button>

            </div>

          </label>

        </form>

      </section>


      {result && (
        <section className="card ingredient-result">

          {result.error ? (
            <div className="error-box">
              {result.error}
            </div>
          ) : (
            <DataObject
              data={result}
            />
          )}

        </section>
      )}


      <section className="card">

        <div className="card-header">

          <div>
            <span className="card-eyebrow">
              KNOWLEDGE BASE
            </span>

            <h3>
              Common Ingredients
            </h3>
          </div>

        </div>


        <div className="ingredient-grid">

          {(ingredients.length
            ? ingredients
            : [
                "Retinoids",
                "Niacinamide",
                "Vitamin C",
                "Hyaluronic Acid",
                "Salicylic Acid",
                "Ceramides",
                "Peptides",
                "AHAs / BHAs",
              ]
          ).map((ingredient) => (

            <div
              className="ingredient-chip"
              key={
                typeof ingredient ===
                "object"
                  ? ingredient.name
                  : ingredient
              }
            >
              <span>
                ◈
              </span>

              {typeof ingredient ===
              "object"
                ? ingredient.name
                : ingredient}

            </div>

          ))}

        </div>

      </section>

    </div>
  );
}


/* ============================================================
   PRODUCTS
============================================================ */

function ProductsPage({
  products,
}) {

  return (
    <div>

      <PageHeader
        eyebrow="PRODUCT INTELLIGENCE"
        title="Recommended Products"
        description="Products selected according to your skin profile, concerns, sensitivity and suitability."
      />


      {products.length === 0 ? (
        <section className="card">
          <EmptyState
            title="No products available yet"
            description="Complete your skin profile and assessment to generate personalized product recommendations."
          />
        </section>
      ) : (
        <div className="product-grid">

          {products.map(
            (product, index) => {

              const name =
                product?.name ||
                product?.product_name ||
                `Recommended Product ${
                  index + 1
                }`;

              const category =
                product?.category ||
                product?.type ||
                "Skincare";

              const score =
                getNumber(
                  product?.score ??
                  product?.suitability_score ??
                  product?.match_score,
                  0
                );

              return (
                <div
                  className="card product-card"
                  key={index}
                >

                  <div className="product-image">
                    ✦
                  </div>

                  <span className="product-category">
                    {category}
                  </span>

                  <h3>
                    {name}
                  </h3>

                  {score > 0 && (
                    <div className="product-score">
                      <span>
                        Suitability
                      </span>

                      <strong>
                        {score > 1
                          ? score.toFixed(0)
                          : (
                              score * 100
                            ).toFixed(0)}
                        %
                      </strong>
                    </div>
                  )}

                  <p>
                    {product?.description ||
                      product?.reason ||
                      "Recommended according to your personalized skincare profile."}
                  </p>

                </div>
              );
            }
          )}

        </div>
      )}

    </div>
  );
}


/* ============================================================
   PROGRESS
============================================================ */

function ProgressPage({
  progress,
  routineItems,
  completedRoutine,
}) {

  const completedRoutineSteps =
    routineItems.filter(
      (item) => completedRoutine[item.id]
    ).length;

  const routinePercentage =
    routineItems.length > 0
      ? Math.round(
          (completedRoutineSteps /
            routineItems.length) *
            100
        )
      : 0;

  const points =
    progress?.history ||
    progress?.data ||
    progress?.records ||
    [];

  return (
    <div>

      <PageHeader
        eyebrow="PROGRESS TRACKING"
        title="Your Skin Progress"
        description="Monitor skin improvement, routine adherence and health-score trends over time."
      />


      <div className="progress-cards">

        <StatCard
          title="Current Score"
          value={
            progress?.current_score
              ? `${progress.current_score}/100`
              : "—"
          }
          subtitle="Latest health score"
          icon="↗"
          accent="green"
        />

        <StatCard
          title="Improvement"
          value={
            progress?.improvement
              ? `${progress.improvement}%`
              : "—"
          }
          subtitle="Compared with previous"
          icon="↑"
          accent="blue"
        />

        <StatCard
          title="Routine"
          value={`${routinePercentage}%`}
          subtitle={`${completedRoutineSteps}/${routineItems.length} steps completed`}
          icon="✓"
          accent="purple"
        />

      </div>


      <section className="card progress-chart-card">

        <div className="card-header">

          <div>
            <span className="card-eyebrow">
              TREND ANALYSIS
            </span>

            <h3>
              Skin Health Trend
            </h3>
          </div>

        </div>


        {points.length === 0 ? (
          <EmptyState
            title="Not enough progress data"
            description="Continue using your routine and record progress to build a meaningful trend."
          />
        ) : (
          <div className="progress-bars">

            {points.map(
              (point, index) => {

                const value =
                  getNumber(
                    point?.score ??
                    point?.health_score,
                    0
                  );

                return (
                  <div
                    className="progress-point"
                    key={index}
                  >

                    <div>
                      <span>
                        {point?.date ||
                          point?.day ||
                          `Day ${
                            index + 1
                          }`}
                      </span>

                      <strong>
                        {value}
                      </strong>
                    </div>

                    <div className="progress-track large">
                      <div
                        className="progress-fill"
                        style={{
                          width: `${Math.min(
                            value,
                            100
                          )}%`,
                        }}
                      />
                    </div>

                  </div>
                );
              }
            )}

          </div>
        )}

      </section>

    </div>
  );
}


/* ============================================================
   REPORTS
============================================================ */

function ReportsPage({
  score,
  profile,
  analysis,
  routine,
  products,
  progress,
}) {

  function downloadReport() {

    const report = {
      title:
        "AI Skin Intelligence Report",

      generated_at:
        new Date().toISOString(),

      skin_health_score:
        score,

      skin_profile:
        profile,

      latest_analysis:
        analysis,

      personalized_routine:
        routine,

      recommended_products:
        products,

      progress:
        progress,
    };


    const blob =
      new Blob(
        [
          JSON.stringify(
            report,
            null,
            2
          ),
        ],
        {
          type:
            "application/json",
        }
      );


    const url =
      URL.createObjectURL(blob);

    const link =
      document.createElement(
        "a"
      );

    link.href = url;

    link.download =
      "skin-intelligence-report.json";

    link.click();

    URL.revokeObjectURL(url);
  }


  return (
    <div>

      <PageHeader
        eyebrow="REPORTS & EXPORT"
        title="Skin Reports"
        description="Review and export your skin assessment, health score, routine, recommendations and progress."
      />


      <div className="report-grid">

        {[
          {
            title:
              "Skin Assessment Report",
            icon: "✦",
            description:
              "Latest AI-assisted skin assessment and predictions.",
          },
          {
            title:
              "Skin Health Report",
            icon: "♡",
            description:
              "Health score and contributing factors.",
          },
          {
            title:
              "Routine Report",
            icon: "✓",
            description:
              "Personalized morning, evening and weekly routine.",
          },
          {
            title:
              "Progress Report",
            icon: "↗",
            description:
              "Skin improvement and routine-adherence tracking.",
          },
        ].map(
          (report) => (
            <div
              className="card report-card"
              key={report.title}
            >

              <div className="report-icon">
                {report.icon}
              </div>

              <h3>
                {report.title}
              </h3>

              <p>
                {report.description}
              </p>

              <button
                className="secondary-button"
                onClick={
                  downloadReport
                }
              >
                Export Report
              </button>

            </div>
          )
        )}

      </div>


      <section className="card export-note">

        <strong>
          Export Center
        </strong>

        <p>
          The current frontend provides
          a structured report export.
          PDF and Excel generation should
          be connected to backend report
          endpoints as the final deployment
          phase.
        </p>

      </section>

    </div>
  );
}


/* ============================================================
   NOTIFICATIONS
============================================================ */

function NotificationsPage() {

  const notifications = [
    {
      title:
        "Morning routine reminder",
      text:
        "Remember to complete your morning skincare routine.",
      time:
        "Today",
    },
    {
      title:
        "Hydration reminder",
      text:
        "Keep your water intake consistent throughout the day.",
      time:
        "Today",
    },
    {
      title:
        "Progress check",
      text:
        "Record your skin progress to improve trend analysis.",
      time:
        "This week",
    },
  ];


  return (
    <div>

      <PageHeader
        eyebrow="REMINDERS"
        title="Notifications"
        description="Routine, hydration, sleep, replenishment and progress reminders."
      />


      <div className="notification-list">

        {notifications.map(
          (notification) => (

            <div
              className="card notification-card"
              key={
                notification.title
              }
            >

              <div className="notification-icon">
                ♢
              </div>

              <div>

                <strong>
                  {notification.title}
                </strong>

                <p>
                  {notification.text}
                </p>

                <small>
                  {notification.time}
                </small>

              </div>

            </div>

          )
        )}

      </div>

    </div>
  );
}


/* ============================================================
   RECOMMENDATIONS
============================================================ */

function RecommendationList({
  items,
}) {

  if (!items?.length) {
    return (
      <EmptyState
        title="No recommendations yet"
        description="Complete your profile and AI assessment to receive personalized recommendations."
      />
    );
  }


  return (
    <div className="recommendation-list">

      {items
        .slice(0, 4)
        .map((item, index) => {

          const title =
            item?.name ||
            item?.title ||
            item?.product_name ||
            `Recommendation ${
              index + 1
            }`;

          const description =
            item?.reason ||
            item?.description ||
            "Personalized recommendation based on your profile.";

          return (
            <div
              className="recommendation-item"
              key={index}
            >

              <div className="recommendation-icon">
                ✦
              </div>

              <div>
                <strong>
                  {title}
                </strong>

                <p>
                  {description}
                </p>
              </div>

            </div>
          );
        })}

    </div>
  );
}


/* ============================================================
   EMPTY STATE
============================================================ */

function EmptyState({
  title,
  description,
}) {

  return (
    <div className="empty-state">

      <div className="empty-state-icon">
        ○
      </div>

      <strong>
        {title}
      </strong>

      <p>
        {description}
      </p>

    </div>
  );
}


/* ============================================================
   DATA OBJECT
============================================================ */

function DataObject({
  data,
}) {

  const entries =
    Object.entries(data || {});


  return (
    <div className="data-object">

      {entries.map(
        ([key, value]) => (

          <div
            className="data-row"
            key={key}
          >

            <span>
              {key.replaceAll(
                "_",
                " "
              )}
            </span>

            <strong>
              {typeof value ===
              "object"
                ? JSON.stringify(
                    value
                  )
                : String(value)}
            </strong>

          </div>

        )
      )}

    </div>
  );
}


export default App;