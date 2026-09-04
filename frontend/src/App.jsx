import React, { useEffect, useMemo, useState } from "react";
import jsPDF from "jspdf";
import * as XLSX from "xlsx";

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
  { id: "dashboard", label: "Dashboard", icon: "⌂" },
  { id: "profile", label: "Skin Profile", icon: "◉" },
  { id: "analysis", label: "AI Skin Analysis", icon: "✦" },
  { id: "routine", label: "My Routine", icon: "✓" },
  { id: "ingredients", label: "Ingredients", icon: "◈" },
  { id: "products", label: "Products", icon: "▣" },
  { id: "progress", label: "Progress", icon: "↗" },
  { id: "reports", label: "Reports", icon: "▤" },
  { id: "notifications", label: "Notifications", icon: "♢" },
];

const CONSULTANT_NAV_ITEMS = [
  { id: "dashboard", label: "Dashboard", icon: "⌂" },
  { id: "clients", label: "Clients", icon: "👥" },
  { id: "client-profile", label: "Client Profiles", icon: "◉" },
  { id: "assessments", label: "AI Assessments", icon: "✦" },
  { id: "recommendations", label: "Recommendations", icon: "◆" },
  { id: "catalog", label: "Products & Ingredients", icon: "◇" },
  { id: "progress", label: "Progress", icon: "↗" },
  { id: "reports", label: "Reports", icon: "▤" },
  { id: "notifications", label: "Notifications", icon: "♢" },
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



function parseWaterIntake(value) {
  if (value === null || value === undefined || value === "") {
    return null;
  }

  if (typeof value === "number") {
    return Number.isFinite(value) ? value : null;
  }

  const match = String(value).match(/(\d+(?:\.\d+)?)/);
  return match ? Number(match[1]) : null;
}


function getProgressRecords(progress) {
  const records =
    progress?.history ||
    progress?.data ||
    progress?.records ||
    [];

  return Array.isArray(records) ? records : [];
}


function getProgressScore(record) {
  return getNumber(
    record?.score ??
    record?.health_score ??
    record?.skin_score,
    NaN
  );
}


function buildNotifications({
  score,
  profile,
  analysis,
  routineItems,
  completedRoutine,
  progress,
}) {
  const notifications = [];
  const now = new Date();

  const addNotification = ({
    id,
    type,
    icon,
    title,
    text,
    priority = "normal",
    time = "Live",
  }) => {
    notifications.push({
      id,
      type,
      icon,
      title,
      text,
      priority,
      time,
    });
  };

  const completedSteps = routineItems.filter(
    (item) => completedRoutine?.[item.id]
  ).length;

  const totalSteps = routineItems.length;

  if (totalSteps > 0 && completedSteps < totalSteps) {
    addNotification({
      id: "routine-progress",
      type: "routine",
      icon: "✓",
      title: "Your routine still has steps to complete",
      text: `${completedSteps} of ${totalSteps} current routine steps are marked complete. Finish the remaining steps to stay consistent.`,
      priority: "high",
    });
  } else if (totalSteps > 0) {
    addNotification({
      id: "routine-complete",
      type: "routine",
      icon: "✓",
      title: "Your current routine is complete",
      text: `All ${totalSteps} personalized routine steps are currently marked complete.`,
    });
  } else {
    addNotification({
      id: "routine-empty",
      type: "routine",
      icon: "✓",
      title: "Your routine is not available yet",
      text: "Complete your skin profile so the system can generate personalized routine steps.",
    });
  }

  const waterIntake = parseWaterIntake(profile?.water_intake);

  if (waterIntake !== null && waterIntake < 2) {
    addNotification({
      id: "hydration",
      type: "wellness",
      icon: "💧",
      title: "Hydration needs attention",
      text: `Your profile currently records about ${waterIntake} L/day. Keeping hydration consistent can support your overall skincare plan.`,
      priority: "high",
    });
  } else if (waterIntake !== null) {
    addNotification({
      id: "hydration-good",
      type: "wellness",
      icon: "💧",
      title: "Hydration is being tracked",
      text: `Your profile records about ${waterIntake} L/day. Keep your intake consistent with your personal routine.`,
    });
  }

  const sleepQuality = String(
    profile?.sleep_quality || ""
  ).toLowerCase();

  if (sleepQuality === "poor" || sleepQuality === "fair") {
    addNotification({
      id: "sleep",
      type: "wellness",
      icon: "☾",
      title: "Sleep quality could use attention",
      text: `Your profile currently records sleep quality as ${profile.sleep_quality}. Improving sleep consistency may support your overall skincare plan.`,
      priority: "high",
    });
  }

  const hasSensitivity =
    String(profile?.allergies || "").trim() ||
    String(profile?.sensitivities || "").trim();

  if (hasSensitivity) {
    addNotification({
      id: "sensitivity",
      type: "safety",
      icon: "!",
      title: "Check ingredients before trying new products",
      text: "Your profile contains allergy or sensitivity information. Review ingredient lists carefully before adding new products.",
      priority: "high",
    });
  }

  const progressRecords = getProgressRecords(progress)
    .map((record) => ({
      ...record,
      _score: getProgressScore(record),
      _date: new Date(
        record?.date ||
        record?.progress_date ||
        record?.created_at ||
        0
      ),
    }))
    .filter((record) => Number.isFinite(record._score))
    .sort((a, b) => a._date - b._date);

  if (progressRecords.length >= 2) {
    const first = progressRecords[0]._score;
    const latest =
      progressRecords[progressRecords.length - 1]._score;
    const change = Number((latest - first).toFixed(1));

    if (change > 0) {
      addNotification({
        id: "progress-improving",
        type: "progress",
        icon: "↗",
        title: "Your skin-health score is improving",
        text: `Your latest recorded score is ${latest.toFixed(1)}/100, up ${change.toFixed(1)} points from your first check-in.`,
      });
    } else if (change < 0) {
      addNotification({
        id: "progress-attention",
        type: "progress",
        icon: "↘",
        title: "Your recent score needs attention",
        text: `Your latest recorded score is ${latest.toFixed(1)}/100, down ${Math.abs(change).toFixed(1)} points from your first check-in. Review your routine and tracked lifestyle factors.`,
        priority: "high",
      });
    } else {
      addNotification({
        id: "progress-stable",
        type: "progress",
        icon: "→",
        title: "Your skin-health score is stable",
        text: `Your latest recorded score is ${latest.toFixed(1)}/100 with no overall change from your first check-in.`,
      });
    }

    const latestDate = progressRecords[progressRecords.length - 1]._date;

    if (
      Number.isFinite(latestDate.getTime()) &&
      now.getTime() - latestDate.getTime() >
        7 * 24 * 60 * 60 * 1000
    ) {
      addNotification({
        id: "progress-check",
        type: "progress",
        icon: "●",
        title: "Time for a new progress check-in",
        text: "Your latest recorded check-in is more than a week old. Add a new check-in to keep your progress trend meaningful.",
      });
    }
  } else {
    addNotification({
      id: "progress-start",
      type: "progress",
      icon: "●",
      title: "Build your progress history",
      text: "Record additional check-ins so the system can compare your skin-health score over time.",
    });
  }

  const ai =
    analysis?.ai_analysis ||
    analysis ||
    {};

  const top =
    ai?.top_prediction ||
    ai?.primary_concern ||
    {};

  const latestConcern =
    top?.label ||
    ai?.condition ||
    ai?.predicted_condition ||
    ai?.prediction;

  if (latestConcern) {
    const confidence =
      top?.confidence_percent ??
      ai?.confidence_percent ??
      (top?.confidence != null
        ? Number(top.confidence) * 100
        : null);

    addNotification({
      id: "analysis-available",
      type: "analysis",
      icon: "✦",
      title: "Your latest AI skin analysis is available",
      text:
        confidence !== null && Number.isFinite(Number(confidence))
          ? `The latest analysis highlights ${latestConcern} as a possible visible concern with ${Number(confidence).toFixed(1)}% confidence.`
          : `The latest analysis highlights ${latestConcern} as a possible visible skincare concern.`,
    });
  } else {
    addNotification({
      id: "analysis-needed",
      type: "analysis",
      icon: "✦",
      title: "Complete an AI skin analysis",
      text: "Upload a clear facial image to add an AI-assisted skin analysis to your personalized plan.",
    });
  }

  if (Number.isFinite(Number(score))) {
    const scoreNumber = Number(score);

    if (scoreNumber < 60) {
      addNotification({
        id: "score-attention",
        type: "health",
        icon: "!",
        title: "Your current skin-health score needs attention",
        text: `Your current score is ${scoreNumber.toFixed(1)}/100. Review your routine, lifestyle and tracked factors for areas that may need improvement.`,
        priority: "high",
      });
    } else if (scoreNumber >= 80) {
      addNotification({
        id: "score-good",
        type: "health",
        icon: "✓",
        title: "Your current skin-health score is strong",
        text: `Your current score is ${scoreNumber.toFixed(1)}/100. Continue following your personalized routine consistently.`,
      });
    }
  }

  return notifications;
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

  const isConsultant = String(user?.role || "user")
    .toLowerCase()
    .includes("consult");

  const currentNavItems = isConsultant
    ? CONSULTANT_NAV_ITEMS
    : NAV_ITEMS;

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



  /*
    Refresh backend-backed data every 30 seconds while
    Notifications is open so its content stays current.
  */
  useEffect(() => {
    if (
      !authenticated ||
      activePage !== "notifications"
    ) {
      return undefined;
    }

    let mounted = true;

    const refreshNotifications = async () => {
      if (!mounted) return;

      try {
        await loadApplicationData();
      } catch {
        // Keep the last successful data visible.
      }
    };

    refreshNotifications();

    const interval = setInterval(
      refreshNotifications,
      30000
    );

    return () => {
      mounted = false;
      clearInterval(interval);
    };
  }, [
    authenticated,
    activePage,
  ]);

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
        role: response.role || "user",
        is_active: response.is_active,
        age: response.age,
        gender: response.gender,
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
     DYNAMIC NOTIFICATIONS
  ========================================================= */

  const notificationItems = useMemo(
    () =>
      buildNotifications({
        score,
        profile,
        analysis,
        routineItems,
        completedRoutine,
        progress,
      }),
    [
      score,
      profile,
      analysis,
      routineItems,
      completedRoutine,
      progress,
    ]
  );


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
        className={`sidebar consultant-sidebar ${
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
              {isConsultant
                ? "Professional Workspace"
                : "Personalized Skincare"}
            </span>
          </div>
        </div>


        <div className="sidebar-section-title">
          MAIN MENU
        </div>


        <nav className="sidebar-nav">

          {currentNavItems.map((item) => (
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
              {currentNavItems.find(
                (item) =>
                  item.id === activePage
              )?.label}
            </span>

            <small>
              AI-assisted skin intelligence
            </small>

          </div>


          <div className="topbar-right">

            <button
              className="notification-button"
              onClick={() =>
                setActivePage("notifications")
              }
              aria-label={`Open notifications. ${notificationItems.length} current notifications.`}
              title="Notifications"
            >
              ♢
              {notificationItems.length > 0 && (
                <span className="notification-badge">
                  {notificationItems.length > 9
                    ? "9+"
                    : notificationItems.length}
                </span>
              )}
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
                String(user?.role || "user").toLowerCase().includes("consult")
                  ? (
                    <ConsultantDashboard
                      user={user}
                      score={score}
                      scoreLabel={scoreLabel}
                      profile={profile}
                      routineItems={routineItems}
                      completedRoutine={completedRoutine}
                      setActivePage={setActivePage}
                      recommendations={recommendations}
                      products={products}
                      analysis={analysis}
                    />
                  )
                  : (
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
                  )
              )}


              {isConsultant && activePage === "clients" && (
                <ConsultantClientsPage
                  user={user}
                  profile={profile}
                  score={score}
                  analysis={analysis}
                  setActivePage={setActivePage}
                />
              )}

              {isConsultant && activePage === "client-profile" && (
                <ConsultantClientProfilePage
                  user={user}
                  profile={profile}
                  score={score}
                  scoreLabel={scoreLabel}
                  setActivePage={setActivePage}
                />
              )}

              {isConsultant && activePage === "assessments" && (
                <ConsultantAssessmentsPage
                  analysis={analysis}
                  selectedImage={selectedImage}
                  imagePreview={imagePreview}
                  setActivePage={setActivePage}
                  onImageChange={handleImageChange}
                  onAnalyze={handleAnalysis}
                  loading={analysisLoading}
                />
              )}

              {isConsultant && activePage === "recommendations" && (
                <ConsultantRecommendationsPage
                  recommendations={recommendations}
                  products={products}
                  setActivePage={setActivePage}
                />
              )}

              {isConsultant && activePage === "catalog" && (
                <ConsultantCatalogPage
                  products={products}
                  ingredients={ingredients}
                  setActivePage={setActivePage}
                />
              )}

              {!isConsultant && activePage === "profile" && (
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
                  completedRoutine={completedRoutine}
                />
              )}


              {activePage === "notifications" && (
                <NotificationsPage
                  notifications={notificationItems}
                />
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
   CONSULTANT ROLE PAGES
============================================================ */

function ConsultantClientsPage({
  user,
  profile,
  score,
  analysis,
  setActivePage,
}) {
  const clientName =
    user?.name || "Demo User";

  const clientEmail =
    user?.email || "";

  const concern =
    profile?.concerns || "Not set";

  const skinType =
    profile?.skin_type || "Not set";

  const assessmentStatus =
    analysis ? "Reviewed" : "Pending";

  return (
    <div className="consultant-client-page">

      <PageHeader
        eyebrow="CLIENT MANAGEMENT"
        title="Clients"
        description="Review client records, assessments and skincare progress from one workspace."
      />

      <section className="consultant-client-card">

        <div className="consultant-client-card-header">

          <div>
            <span className="consultant-card-eyebrow">
              CLIENT LIST
            </span>

            <h3>
              Active Client
            </h3>
          </div>

          <span className="consultant-client-count">
            1 client
          </span>

        </div>

        <div className="consultant-client-content">

          <div className="consultant-client-identity">

            <div className="consultant-client-avatar">
              {(clientName || "D")
                .charAt(0)
                .toUpperCase()}
            </div>

            <div>
              <h4>
                {clientName}
              </h4>

              <p>
                {clientEmail}
              </p>

              <span className="consultant-client-status">
                <span className="consultant-status-dot" />
                Active client
              </span>
            </div>

          </div>

          <div className="consultant-client-stats">

            <div className="consultant-client-stat">
              <span>
                SKIN TYPE
              </span>

              <strong>
                {skinType}
              </strong>
            </div>

            <div className="consultant-client-stat">
              <span>
                TOP CONCERN
              </span>

              <strong>
                {concern}
              </strong>
            </div>

            <div className="consultant-client-stat">
              <span>
                HEALTH SCORE
              </span>

              <strong className="consultant-score">
                {score}/100
              </strong>
            </div>

            <div className="consultant-client-stat">
              <span>
                ASSESSMENT
              </span>

              <strong
                className={
                  assessmentStatus === "Reviewed"
                    ? "consultant-reviewed"
                    : "consultant-pending"
                }
              >
                {assessmentStatus}
              </strong>
            </div>

          </div>

          <div className="consultant-client-action">

            <button
              className="consultant-open-profile"
              onClick={() =>
                setActivePage(
                  "client-profile"
                )
              }
            >
              Open profile
              <span>→</span>
            </button>

          </div>

        </div>

      </section>

      <section className="consultant-client-info">

        <div className="consultant-info-icon">
          ✦
        </div>

        <div>
          <strong>
            Consultant review workspace
          </strong>

          <p>
            Review the client's profile first,
            then move to the AI assessment and
            recommendations. AI results are
            supportive insights and not a medical
            diagnosis.
          </p>
        </div>

      </section>

    </div>
  );
}

function ConsultantClientProfilePage({ user, profile, score, scoreLabel, setActivePage }) {
  const profileFields = [
    ["Skin Type", profile?.skin_type || "Not set"],
    ["Age Group", profile?.age_group || "Not set"],
    ["Skin Concerns", profile?.skin_concerns || profile?.concerns || "Not set"],
    ["Allergies", profile?.allergies || "None provided"],
    ["Sensitivities", profile?.sensitivities || "None provided"],
    ["Lifestyle", profile?.lifestyle_habits || profile?.lifestyle || "Not set"],
    ["Sleep Quality", profile?.sleep_quality || "Not set"],
    ["Water Intake", profile?.water_intake ? `${profile.water_intake} L/day` : "Not set"],
    ["Environmental Exposure", profile?.environmental_exposure || "Not set"],
  ];

  const scoreValue = Math.max(0, Math.min(100, Math.round(Number(score) || 0)));

  return (
    <div>
      <PageHeader
        eyebrow="CLIENT PROFILE"
        title={user?.name || "Client Profile"}
        description="Review the client's skincare profile and health factors before making recommendations."
      />

      <div
        style={{
          display: "grid",
          gridTemplateColumns: "minmax(260px, 0.8fr) minmax(420px, 1.5fr)",
          gap: "20px",
          alignItems: "stretch",
          marginTop: "20px",
        }}
      >
        <section
          className="card"
          style={{
            padding: "24px",
            display: "flex",
            flexDirection: "column",
            minHeight: "100%",
          }}
        >
          <div className="card-header" style={{ marginBottom: "18px" }}>
            <div>
              <span className="card-eyebrow">SKIN HEALTH</span>
              <h3 style={{ marginTop: "6px" }}>Health Score</h3>
            </div>
            <strong style={{ fontSize: "26px", whiteSpace: "nowrap" }}>
              {scoreValue}/100
            </strong>
          </div>

          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: "18px",
              padding: "18px",
              borderRadius: "18px",
              background: "linear-gradient(135deg, rgba(35,174,111,0.08), rgba(247,250,248,0.9))",
              border: "1px solid rgba(35,174,111,0.10)",
              marginBottom: "18px",
            }}
          >
            <div
              style={{
                width: "72px",
                height: "72px",
                borderRadius: "50%",
                background: `conic-gradient(#23ae6f ${scoreValue * 3.6}deg, #e6f1eb ${scoreValue * 3.6}deg)`,
                display: "grid",
                placeItems: "center",
                flex: "0 0 auto",
              }}
            >
              <div
                style={{
                  width: "58px",
                  height: "58px",
                  borderRadius: "50%",
                  background: "#ffffff",
                  display: "grid",
                  placeItems: "center",
                  fontWeight: 800,
                  color: "#1f3028",
                  fontSize: "16px",
                }}
              >
                {scoreValue}
              </div>
            </div>

            <div style={{ minWidth: 0 }}>
              <strong
                style={{
                  display: "block",
                  fontSize: "18px",
                  color: "#23352d",
                  marginBottom: "5px",
                }}
              >
                {scoreLabel}
              </strong>
              <p
                className="muted-text"
                style={{ margin: 0, lineHeight: 1.55 }}
              >
                Overall skin-health indicator based on the available profile,
                assessment and routine information.
              </p>
            </div>
          </div>

          <button
            className="primary-button"
            onClick={() => setActivePage("assessments")}
            style={{ marginTop: "auto", width: "100%" }}
          >
            Review AI Assessment →
          </button>
        </section>

        <section
          className="card"
          style={{
            padding: "24px",
            minWidth: 0,
          }}
        >
          <div className="card-header" style={{ marginBottom: "18px" }}>
            <div>
              <span className="card-eyebrow">CLIENT DETAILS</span>
              <h3 style={{ marginTop: "6px" }}>Profile Information</h3>
            </div>
          </div>

          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(2, minmax(0, 1fr))",
              gap: "12px",
            }}
          >
            {profileFields.map(([label, value]) => (
              <div
                key={label}
                style={{
                  minWidth: 0,
                  padding: "15px 16px",
                  borderRadius: "15px",
                  background: "linear-gradient(135deg, #f7fbf8, #fffaf7)",
                  border: "1px solid rgba(49,75,64,0.08)",
                }}
              >
                <span
                  style={{
                    display: "block",
                    marginBottom: "7px",
                    color: "#77847e",
                    fontSize: "10px",
                    fontWeight: 700,
                    letterSpacing: "0.08em",
                    textTransform: "uppercase",
                  }}
                >
                  {label}
                </span>
                <strong
                  style={{
                    display: "block",
                    color: "#26372f",
                    fontSize: "14px",
                    lineHeight: 1.45,
                    overflowWrap: "anywhere",
                  }}
                >
                  {value}
                </strong>
              </div>
            ))}
          </div>
        </section>
      </div>

      <section
        className="card"
        style={{
          marginTop: "20px",
          padding: "18px 20px",
          background: "rgba(255,255,255,0.72)",
        }}
      >
        <div style={{ display: "flex", gap: "12px", alignItems: "flex-start" }}>
          <div
            style={{
              width: "34px",
              height: "34px",
              borderRadius: "11px",
              display: "grid",
              placeItems: "center",
              background: "rgba(35,174,111,0.10)",
              color: "#15905b",
              flex: "0 0 auto",
              fontWeight: 800,
            }}
          >
            ✓
          </div>
          <div>
            <strong style={{ display: "block", color: "#26372f", marginBottom: "4px" }}>
              Consultant review workspace
            </strong>
            <p className="muted-text" style={{ margin: 0, lineHeight: 1.55 }}>
              Review the client's profile first, then move to the AI assessment and recommendations. AI results are supportive insights and not a medical diagnosis.
            </p>
          </div>
        </div>
      </section>
    </div>
  );
}

function ConsultantAssessmentsPage({ analysis, selectedImage, imagePreview, setActivePage, onImageChange, onAnalyze, loading }) {
  const top = analysis?.ai_analysis?.top_prediction || analysis?.top_prediction || analysis?.primary_concern;
  return (
    <div>
      <PageHeader eyebrow="AI REVIEW" title="AI Assessments" description="Review AI-assisted facial skin assessments before discussing recommendations with the client." />
      <div className="dashboard-two-column">
        <section className="card">
          <div className="card-header"><div><span className="card-eyebrow">ASSESSMENT INPUT</span><h3>Client Image</h3></div></div>
          <input type="file" accept="image/*" onChange={onImageChange} />
          {imagePreview && <img src={imagePreview} alt="Client preview" style={{ width: "100%", maxHeight: 320, objectFit: "cover", borderRadius: 18, marginTop: 16 }} />}
          <button className="primary-button" style={{ marginTop: 16 }} onClick={onAnalyze} disabled={!selectedImage || loading}>
            {loading ? "Analyzing..." : "Run AI Assessment"}
          </button>
        </section>

        <section className="card">
          <div className="card-header"><div><span className="card-eyebrow">LATEST RESULT</span><h3>{top?.label || "No assessment yet"}</h3></div></div>
          {top ? (
            <><div className="score-highlight">{Number(top.confidence_percent ?? (top.confidence || 0) * 100).toFixed(1)}%</div><p className="muted-text">Possible visible skincare concern. Review the image and client history together.</p></>
          ) : <p className="muted-text">Run an assessment to see the latest AI-assisted result.</p>}
          <button className="small-link" onClick={() => setActivePage("recommendations")}>Continue to recommendations →</button>
        </section>
      </div>
      <section className="card" style={{ marginTop: 20 }}>
        <span className="card-eyebrow">IMPORTANT</span>
        <p className="muted-text">AI results are supportive skincare insights only and are not a medical diagnosis. A qualified healthcare professional should evaluate suspected medical conditions.</p>
      </section>
    </div>
  );
}

function ConsultantRecommendationsPage({ recommendations, products, setActivePage }) {
  const items = recommendations?.length ? recommendations : products || [];
  return (
    <div>
      <PageHeader eyebrow="PERSONALIZED CARE" title="Recommendations" description="Review skincare recommendations and prepare practical guidance for the client." />
      <section className="card">
        <div className="card-header"><div><span className="card-eyebrow">RECOMMENDATION QUEUE</span><h3>{items.length || 0} recommendations available</h3></div><button className="small-link" onClick={() => setActivePage("catalog")}>Browse products →</button></div>
        {items.length ? <RecommendationList items={items} /> : <p className="muted-text">Complete the client profile and assessment to generate more personalized recommendations.</p>}
      </section>
    </div>
  );
}

function ConsultantCatalogPage({ products, ingredients, setActivePage }) {
  return (
    <div>
      <PageHeader eyebrow="PRODUCT INTELLIGENCE" title="Products & Ingredients" description="Use product and ingredient information to support safer, more personalized skincare recommendations." />
      <div className="dashboard-two-column">
        <section className="card">
          <div className="card-header"><div><span className="card-eyebrow">PRODUCTS</span><h3>Recommended Products</h3></div></div>
          {products?.length ? <RecommendationList items={products.slice(0, 6)} /> : <p className="muted-text">No product recommendations available yet.</p>}
        </section>
        <section className="card">
          <div className="card-header"><div><span className="card-eyebrow">INGREDIENTS</span><h3>Ingredient Library</h3></div><button className="small-link" onClick={() => setActivePage("recommendations")}>Use in recommendations</button></div>
          {ingredients?.length ? <RecommendationList items={ingredients.slice(0, 6)} /> : <p className="muted-text">Use the ingredient analyzer from the User workflow to evaluate a specific ingredient.</p>}
        </section>
      </div>
    </div>
  );
}

/* ============================================================
   CONSULTANT DASHBOARD
============================================================ */

function ConsultantDashboard({
  user,
  score,
  scoreLabel,
  profile,
  routineItems,
  completedRoutine,
  setActivePage,
  recommendations,
  products,
  analysis,
}) {
  const completedSteps = routineItems.filter(
    (item) => completedRoutine[item.id]
  ).length;

  const routinePercentage =
    routineItems.length > 0
      ? Math.round(
          (completedSteps / routineItems.length) * 100
        )
      : 0;

  const concerns = normalizeArray(profile?.concerns);

  const profileComplete = Boolean(
    profile?.id ||
    profile?.skin_type ||
    profile?.concerns
  );

  const assessmentReady = Boolean(analysis);

  const recommendationCount =
    recommendations.length || products.length;

  const clientAttention =
    !profileComplete || !assessmentReady
      ? "Profile or assessment needs review"
      : score < 60
        ? "Skin health score needs attention"
        : "No immediate attention flag";

  const roleBadge =
    String(user?.role || "")
      .toLowerCase()
      .includes("consult")
      ? "Skincare Consultant"
      : "Professional Workspace";

  return (
    <div className="consultant-dashboard">
      <PageHeader
        eyebrow="PROFESSIONAL WORKSPACE"
        title={`Good day, ${user?.name || "Consultant"} 👋`}
        description="Review client skincare information, AI-assisted assessments and personalized recommendations from one workspace."
      />

      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: "10px",
          marginBottom: "22px",
          flexWrap: "wrap",
        }}
      >
        <span
          className="soft-badge"
          style={{
            padding: "8px 14px",
            borderRadius: "999px",
          }}
        >
          ✦ {roleBadge}
        </span>

        <span
          style={{
            fontSize: "13px",
            color: "#66756f",
          }}
        >
          Professional skincare review workspace
        </span>
      </div>

      <div className="dashboard-grid">
        <StatCard
          title="Active Client"
          value={user?.name || "Current client"}
          subtitle="Current workspace"
          icon="♙"
          accent="green"
        />

        <StatCard
          title="Skin Health"
          value={`${Math.round(score)}/100`}
          subtitle={scoreLabel}
          icon="♡"
          accent="blue"
        />

        <StatCard
          title="AI Assessment"
          value={assessmentReady ? "Ready" : "Pending"}
          subtitle={
            assessmentReady
              ? "Latest assessment available"
              : "Assessment required"
          }
          icon="✦"
          accent="orange"
        />

        <StatCard
          title="Recommendations"
          value={recommendationCount}
          subtitle="Available for review"
          icon="✓"
          accent="purple"
        />
      </div>

      <div className="dashboard-two-column">
        <section className="card">
          <div className="card-header">
            <div>
              <span className="card-eyebrow">
                CLIENT PROFILE
              </span>
              <h3>Skin Information</h3>
            </div>

            <button
              className="small-link"
              onClick={() => setActivePage("client-profile")}
            >
              Open profile
            </button>
          </div>

          <div
            style={{
              display: "grid",
              gridTemplateColumns:
                "repeat(auto-fit, minmax(150px, 1fr))",
              gap: "12px",
            }}
          >
            {[
              [
                "Skin Type",
                profile?.skin_type || "Not set",
              ],
              [
                "Age Group",
                profile?.age_group || "Not set",
              ],
              [
                "Top Concern",
                concerns[0] || "Not identified",
              ],
              [
                "Sleep",
                profile?.sleep_quality || "Not set",
              ],
            ].map(([label, value]) => (
              <div
                key={label}
                style={{
                  padding: "16px",
                  borderRadius: "16px",
                  background:
                    "linear-gradient(135deg, #f7fbf8, #fffaf7)",
                  border: "1px solid rgba(31, 95, 72, 0.08)",
                }}
              >
                <small
                  style={{
                    display: "block",
                    color: "#7a8983",
                    marginBottom: "7px",
                    fontSize: "11px",
                    fontWeight: 700,
                    letterSpacing: "0.08em",
                    textTransform: "uppercase",
                  }}
                >
                  {label}
                </small>
                <strong
                  style={{
                    display: "block",
                    color: "#18352a",
                    fontSize: "16px",
                  }}
                >
                  {value}
                </strong>
              </div>
            ))}
          </div>
        </section>

        <section className="card health-card">
          <div className="card-header">
            <div>
              <span className="card-eyebrow">
                ASSESSMENT OVERVIEW
              </span>
              <h3>Skin Health Review</h3>
            </div>

            <span className="soft-badge">
              {scoreLabel}
            </span>
          </div>

          <div className="score-area">
            <div
              className="score-ring"
              style={{
                "--score": `${score}%`,
              }}
            >
              <div>
                <strong>{Math.round(score)}</strong>
                <span>/100</span>
              </div>
            </div>

            <div className="score-details">
              <p>
                Review the user's skin condition,
                lifestyle, sleep, hydration and
                routine consistency before making
                skincare recommendations.
              </p>

              <button
                className="text-button"
                onClick={() => setActivePage("assessments")}
              >
                Review AI assessment →
              </button>
            </div>
          </div>
        </section>
      </div>

      <div className="dashboard-two-column">
        <section className="card">
          <div className="card-header">
            <div>
              <span className="card-eyebrow">
                CLIENT ATTENTION
              </span>
              <h3>Review Queue</h3>
            </div>
          </div>

          <div
            style={{
              display: "flex",
              gap: "14px",
              alignItems: "flex-start",
              padding: "18px",
              borderRadius: "18px",
              background:
                score < 60 || !profileComplete
                  ? "linear-gradient(135deg, #fff8ee, #fffdf8)"
                  : "linear-gradient(135deg, #f2fbf6, #fbfffd)",
              border:
                "1px solid rgba(31, 95, 72, 0.08)",
            }}
          >
            <div
              style={{
                width: "42px",
                height: "42px",
                minWidth: "42px",
                borderRadius: "14px",
                display: "grid",
                placeItems: "center",
                background: "#e7f5ed",
                color: "#1f8a5b",
                fontWeight: 800,
              }}
            >
              !
            </div>

            <div>
              <strong
                style={{
                  display: "block",
                  marginBottom: "6px",
                  color: "#18352a",
                }}
              >
                {clientAttention}
              </strong>

              <p
                style={{
                  margin: 0,
                  color: "#687870",
                  lineHeight: 1.6,
                }}
              >
                {score < 60
                  ? "Review the health factors and current recommendations before the next consultation."
                  : !profileComplete
                    ? "Complete the client profile to improve personalization."
                    : !assessmentReady
                      ? "Run an AI-assisted image assessment for additional visible skin insights."
                      : "The current client record has the key information needed for a skincare review."}
              </p>
            </div>
          </div>
        </section>

        <section className="card">
          <div className="card-header">
            <div>
              <span className="card-eyebrow">
                RECOMMENDATION MANAGEMENT
              </span>
              <h3>Recommendations</h3>
            </div>

            <button
              className="small-link"
              onClick={() => setActivePage("catalog")}
            >
              View products
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

      <section className="card">
        <div className="card-header">
          <div>
            <span className="card-eyebrow">
              CONSULTATION ACTIONS
            </span>
            <h3>Quick Actions</h3>
          </div>
        </div>

        <div
          style={{
            display: "grid",
            gridTemplateColumns:
              "repeat(auto-fit, minmax(190px, 1fr))",
            gap: "12px",
          }}
        >
          {[
            [
              "✦",
              "Review AI Assessment",
              "analysis",
              "Inspect the latest AI-assisted skin assessment.",
            ],
            [
              "◉",
              "Open Client Profile",
              "profile",
              "Review skin type, concerns and lifestyle information.",
            ],
            [
              "✓",
              "Review Routine",
              "routine",
              "Check the personalized morning and evening routine.",
            ],
            [
              "▣",
              "Review Products",
              "products",
              "Inspect product suitability and recommendations.",
            ],
          ].map(([icon, title, page, description]) => (
            <button
              key={page}
              onClick={() => setActivePage(page)}
              style={{
                textAlign: "left",
                border: "1px solid rgba(31, 95, 72, 0.08)",
                borderRadius: "18px",
                padding: "18px",
                background: "#ffffff",
                cursor: "pointer",
                boxShadow:
                  "0 8px 24px rgba(24, 53, 42, 0.05)",
              }}
            >
              <span
                style={{
                  width: "38px",
                  height: "38px",
                  display: "grid",
                  placeItems: "center",
                  borderRadius: "12px",
                  background: "#edf8f1",
                  color: "#1f8a5b",
                  marginBottom: "12px",
                  fontWeight: 800,
                }}
              >
                {icon}
              </span>

              <strong
                style={{
                  display: "block",
                  color: "#18352a",
                  marginBottom: "6px",
                }}
              >
                {title}
              </strong>

              <small
                style={{
                  display: "block",
                  color: "#75837d",
                  lineHeight: 1.5,
                }}
              >
                {description}
              </small>
            </button>
          ))}
        </div>
      </section>

      <div
        style={{
          marginTop: "14px",
          padding: "14px 16px",
          borderRadius: "14px",
          background: "#f6faf7",
          color: "#6c7b74",
          fontSize: "12px",
          lineHeight: 1.6,
        }}
      >
        <strong style={{ color: "#294b3d" }}>
          Professional note:
        </strong>{" "}
        AI results are decision-support information and
        should not be treated as a medical diagnosis.
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
  const [liveProgress, setLiveProgress] =
    useState(progress);

  const [lastUpdated, setLastUpdated] =
    useState(new Date());

  const [refreshing, setRefreshing] =
    useState(false);

  /*
    Real-time progress refresh:
    The page asks the backend for fresh progress data
    every 30 seconds while this page is open.
  */
  useEffect(() => {
    setLiveProgress(progress);
  }, [progress]);

  useEffect(() => {
    let mounted = true;

    async function refreshProgress() {
      if (!mounted) return;

      try {
        setRefreshing(true);

        const freshProgress =
          await getProgress();

        if (mounted) {
          setLiveProgress(
            freshProgress
          );
          setLastUpdated(
            new Date()
          );
        }
      } catch {
        // Keep the last successful data visible.
      } finally {
        if (mounted) {
          setRefreshing(false);
        }
      }
    }

    refreshProgress();

    const interval = setInterval(
      refreshProgress,
      30000
    );

    return () => {
      mounted = false;
      clearInterval(interval);
    };
  }, []);

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

  const points = (
    liveProgress?.history ||
    liveProgress?.data ||
    liveProgress?.records ||
    []
  )
    .map((point, index) => ({
      ...point,
      _index: index,
      _score: getNumber(
        point?.score ??
        point?.health_score ??
        point?.skin_score,
        0
      ),
    }))
    .filter(
      (point) =>
        Number.isFinite(point._score)
    )
    .sort((a, b) => {
      const dateA = new Date(
        a?.date ||
        a?.progress_date ||
        a?.created_at ||
        0
      ).getTime();

      const dateB = new Date(
        b?.date ||
        b?.progress_date ||
        b?.created_at ||
        0
      ).getTime();

      if (
        Number.isFinite(dateA) &&
        Number.isFinite(dateB) &&
        dateA !== dateB
      ) {
        return dateA - dateB;
      }

      return a._index - b._index;
    });

  const chartPoints =
    points.slice(-7);

  const latestPoint =
    chartPoints.length > 0
      ? chartPoints[
          chartPoints.length - 1
        ]
      : null;

  const firstPoint =
    chartPoints.length > 0
      ? chartPoints[0]
      : null;

  const latestScore =
    liveProgress?.current_score !==
      undefined &&
    liveProgress?.current_score !== null
      ? getNumber(
          liveProgress.current_score,
          0
        )
      : latestPoint
        ? latestPoint._score
        : null;

  const firstScore =
    firstPoint
      ? firstPoint._score
      : null;

  const changeFromFirst =
    firstScore !== null &&
    latestScore !== null
      ? Number(
          (
            latestScore -
            firstScore
          ).toFixed(1)
        )
      : null;

  const previousScore =
    chartPoints.length > 1
      ? chartPoints[
          chartPoints.length - 2
        ]._score
      : null;

  const changeFromPrevious =
    previousScore !== null &&
    latestScore !== null
      ? Number(
          (
            latestScore -
            previousScore
          ).toFixed(1)
        )
      : null;

  const averageScore =
    chartPoints.length > 0
      ? Number(
          (
            chartPoints.reduce(
              (sum, point) =>
                sum + point._score,
              0
            ) /
            chartPoints.length
          ).toFixed(1)
        )
      : null;

  const bestScore =
    chartPoints.length > 0
      ? Math.max(
          ...chartPoints.map(
            (point) =>
              point._score
          )
        )
      : null;

  const scoreStatus = (
    score
  ) => {
    if (score === null) {
      return "Waiting for data";
    }

    if (score >= 85) {
      return "Excellent";
    }

    if (score >= 70) {
      return "Good";
    }

    if (score >= 50) {
      return "Needs attention";
    }

    return "Needs improvement";
  };

  const status =
    scoreStatus(latestScore);

  const statusDescription =
    latestScore === null
      ? "Complete your profile and routine check-ins to start building your progress history."
      : latestScore >= 85
        ? "Your tracked skincare factors are currently in a strong range. Keep following your personalized routine consistently."
        : latestScore >= 70
          ? "Your overall tracked skincare factors are looking good. Consistency can help maintain or improve your score."
          : latestScore >= 50
            ? "There is room to improve the factors tracked by the system. Focus on routine consistency, hydration and lifestyle factors."
            : "Several tracked factors could be improved. Review your personalized routine and profile factors.";

  const formatDate = (
    point,
    includeTime = false
  ) => {
    const raw =
      point?.date ||
      point?.progress_date ||
      point?.created_at;

    if (!raw) {
      return "Check-in";
    }

    const date =
      new Date(raw);

    if (
      Number.isNaN(
        date.getTime()
      )
    ) {
      return String(raw);
    }

    return date.toLocaleDateString(
      undefined,
      {
        day: "2-digit",
        month: "short",
        year: "numeric",
        ...(includeTime
          ? {
              hour: "2-digit",
              minute: "2-digit",
            }
          : {}),
      }
    );
  };

  const formatUpdatedTime =
    lastUpdated.toLocaleString(
      undefined,
      {
        day: "2-digit",
        month: "short",
        year: "numeric",
        hour: "2-digit",
        minute: "2-digit",
      }
    );

  /*
    SVG chart coordinates.
    This avoids installing another chart library.
  */
  const chartWidth = 760;
  const chartHeight = 330;
  const chartLeft = 58;
  const chartRight = 22;
  const chartTop = 28;
  const chartBottom = 58;
  const plotWidth =
    chartWidth -
    chartLeft -
    chartRight;
  const plotHeight =
    chartHeight -
    chartTop -
    chartBottom;

  const getX = (index) => {
    if (chartPoints.length <= 1) {
      return (
        chartLeft +
        plotWidth / 2
      );
    }

    return (
      chartLeft +
      (index /
        (chartPoints.length - 1)) *
        plotWidth
    );
  };

  const getY = (score) =>
    chartTop +
    (1 - score / 100) *
      plotHeight;

  const linePath =
    chartPoints.length > 0
      ? chartPoints
          .map(
            (point, index) =>
              `${index === 0 ? "M" : "L"} ${getX(
                index
              )} ${getY(
                point._score
              )}`
          )
          .join(" ")
      : "";

  const areaPath =
    chartPoints.length > 0
      ? `${linePath} L ${getX(
          chartPoints.length - 1
        )} ${
          chartTop +
          plotHeight
        } L ${getX(0)} ${
          chartTop +
          plotHeight
        } Z`
      : "";

  const distribution = {
    excellent: chartPoints.filter(
      (point) =>
        point._score >= 80
    ).length,
    good: chartPoints.filter(
      (point) =>
        point._score >= 60 &&
        point._score < 80
    ).length,
    fair: chartPoints.filter(
      (point) =>
        point._score >= 40 &&
        point._score < 60
    ).length,
    attention: chartPoints.filter(
      (point) =>
        point._score < 40
    ).length,
  };

  const totalCheckIns =
    chartPoints.length;

  const excellentPercentage =
    totalCheckIns > 0
      ? Math.round(
          (distribution.excellent /
            totalCheckIns) *
            100
        )
      : 0;

  return (
    <div className="progress-page">

      <PageHeader
        eyebrow="PROGRESS TRACKING"
        title="Your Skin Progress"
        description="Track your skin-health score, routine consistency and real changes over time."
      />

      <div className="progress-live-status">
        <span className="live-dot" />
        <span>
          {refreshing
            ? "Updating your progress..."
            : `Last updated ${formatUpdatedTime}`}
        </span>

        <span className="live-refresh-text">
          Automatically refreshes every 30 seconds
        </span>
      </div>


      <div className="progress-cards">

        <StatCard
          title="Current Health Score"
          value={
            latestScore !== null
              ? `${latestScore.toFixed(1)}/100`
              : "—"
          }
          subtitle={status}
          icon="♡"
          accent="green"
        />

        <StatCard
          title="Total Improvement"
          value={
            changeFromFirst !== null
              ? `${
                  changeFromFirst > 0
                    ? "+"
                    : ""
                }${changeFromFirst}`
              : "—"
          }
          subtitle={
            changeFromFirst !== null
              ? `Since first check-in (${firstScore?.toFixed(
                  1
                )} → ${latestScore?.toFixed(
                  1
                )})`
              : "Waiting for more history"
          }
          icon="▥"
          accent="blue"
        />

        <StatCard
          title="Routine Completion"
          value={`${routinePercentage}%`}
          subtitle={`${completedRoutineSteps}/${routineItems.length} steps completed`}
          icon="✓"
          accent="purple"
        />

        <StatCard
          title="Total Check-ins"
          value={totalCheckIns}
          subtitle={
            totalCheckIns > 0
              ? "Recent progress records"
              : "No check-ins yet"
          }
          icon="▣"
          accent="green"
        />

      </div>


      <div className="progress-main-grid">

        <section className="card progress-trend-card">

          <div className="progress-section-header">

            <div>
              <span className="card-eyebrow">
                YOUR PROGRESS
              </span>

              <h3>
                Skin Health Trend
              </h3>

              <p>
                Your health score at each recorded
                check-in. A higher score means the
                tracked skincare factors are more
                favorable.
              </p>
            </div>

            <div className="trend-current-score">
              <strong>
                {latestScore !== null
                  ? latestScore.toFixed(1)
                  : "—"}
              </strong>

              <span>/100</span>

              <small>
                {changeFromPrevious === null
                  ? "First check-in"
                  : changeFromPrevious > 0
                    ? `↑ ${changeFromPrevious} vs previous`
                    : changeFromPrevious < 0
                      ? `↓ ${Math.abs(
                          changeFromPrevious
                        )} vs previous`
                      : "→ No change"}
              </small>
            </div>

          </div>


          {chartPoints.length === 0 ? (
            <EmptyState
              title="Not enough progress data"
              description="Your graph will appear here after the application records progress check-ins."
            />
          ) : (
            <div className="skin-chart-wrapper">

              <svg
                className="skin-chart"
                viewBox={`0 0 ${chartWidth} ${chartHeight}`}
                role="img"
                aria-label="Skin health score over time"
              >

                {[0, 20, 40, 60, 80, 100].map(
                  (value) => {
                    const y =
                      getY(value);

                    return (
                      <g
                        key={value}
                      >
                        <line
                          x1={chartLeft}
                          y1={y}
                          x2={
                            chartWidth -
                            chartRight
                          }
                          y2={y}
                          className="chart-grid-line"
                        />

                        <text
                          x={chartLeft - 12}
                          y={y + 4}
                          textAnchor="end"
                          className="chart-axis-label"
                        >
                          {value}
                        </text>
                      </g>
                    );
                  }
                )}


                <path
                  d={areaPath}
                  className="chart-area"
                />

                <path
                  d={linePath}
                  className="chart-line"
                />


                {chartPoints.map(
                  (point, index) => {
                    const x =
                      getX(index);
                    const y =
                      getY(
                        point._score
                      );

                    return (
                      <g
                        key={
                          `${point._index}-${index}`
                        }
                      >

                        <circle
                          cx={x}
                          cy={y}
                          r="7"
                          className="chart-point-outer"
                        />

                        <circle
                          cx={x}
                          cy={y}
                          r="4"
                          className="chart-point-inner"
                        />

                        <text
                          x={x}
                          y={y - 14}
                          textAnchor="middle"
                          className="chart-value-label"
                        >
                          {point._score.toFixed(
                            1
                          )}
                        </text>

                        <text
                          x={x}
                          y={
                            chartTop +
                            plotHeight +
                            25
                          }
                          textAnchor="middle"
                          className="chart-date-label"
                        >
                          {formatDate(
                            point
                          )
                            .replace(
                              /\s\d{4}$/,
                              ""
                            )}
                        </text>

                      </g>
                    );
                  }
                )}

              </svg>

              <div className="chart-legend">
                <span className="chart-legend-dot" />
                <span>Health Score</span>
              </div>

            </div>
          )}

        </section>


        <section className="card score-distribution-card">

          <div className="progress-section-header compact">

            <div>
              <span className="card-eyebrow">
                SCORE DISTRIBUTION
              </span>

              <h3>
                Your Check-ins
              </h3>

              <p>
                See how often your recorded scores
                fall into each range.
              </p>
            </div>

          </div>


          <div className="distribution-total">
            <strong>
              {totalCheckIns}
            </strong>

            <span>
              check-ins
            </span>
          </div>


          <div className="distribution-list">

            <div className="distribution-row">
              <span>
                <i className="distribution-dot excellent" />
                Excellent (80–100)
              </span>

              <strong>
                {distribution.excellent}
              </strong>
            </div>

            <div className="distribution-row">
              <span>
                <i className="distribution-dot good" />
                Good (60–79)
              </span>

              <strong>
                {distribution.good}
              </strong>
            </div>

            <div className="distribution-row">
              <span>
                <i className="distribution-dot fair" />
                Fair (40–59)
              </span>

              <strong>
                {distribution.fair}
              </strong>
            </div>

            <div className="distribution-row">
              <span>
                <i className="distribution-dot attention" />
                Needs attention (0–39)
              </span>

              <strong>
                {distribution.attention}
              </strong>
            </div>

          </div>


          <div className="distribution-insight">
            <strong>
              {excellentPercentage}% of your recent
              check-ins are Excellent
            </strong>

            <span>
              {excellentPercentage >= 70
                ? "Keep following your personalized routine consistently."
                : "Focus on routine consistency and the improvement areas shown below."}
            </span>
          </div>

        </section>

      </div>


      <div className="progress-secondary-grid">

        <section className="card recent-checkins-card">

          <div className="progress-section-header compact">

            <div>
              <span className="card-eyebrow">
                RECENT CHECK-INS
              </span>

              <h3>
                Your Latest Progress
              </h3>
            </div>

          </div>


          {chartPoints.length === 0 ? (
            <EmptyState
              title="No check-ins yet"
              description="Progress records will appear here automatically."
            />
          ) : (
            <div className="checkin-table">

              <div className="checkin-table-header">
                <span>Date & Time</span>
                <span>Score</span>
                <span>Change</span>
                <span>Status</span>
              </div>

              {[
                ...chartPoints,
              ]
                .reverse()
                .map(
                  (point, reverseIndex) => {
                    const originalIndex =
                      chartPoints.length -
                      1 -
                      reverseIndex;

                    const previous =
                      originalIndex > 0
                        ? chartPoints[
                            originalIndex -
                              1
                          ]._score
                        : null;

                    const change =
                      previous !== null
                        ? Number(
                            (
                              point._score -
                              previous
                            ).toFixed(1)
                          )
                        : null;

                    return (
                      <div
                        className="checkin-row"
                        key={`${point._index}-${reverseIndex}`}
                      >

                        <span>
                          {formatDate(
                            point,
                            true
                          )}
                        </span>

                        <strong>
                          {point._score.toFixed(
                            1
                          )}
                        </strong>

                        <span
                          className={
                            change > 0
                              ? "change-positive"
                              : change < 0
                                ? "change-negative"
                                : "change-neutral"
                          }
                        >
                          {change === null
                            ? "—"
                            : change > 0
                              ? `↑ ${change}`
                              : change < 0
                                ? `↓ ${Math.abs(
                                    change
                                  )}`
                                : "→ 0"}
                        </span>

                        <span className="checkin-status">
                          <i
                            className={
                              point._score >=
                              80
                                ? "status-excellent"
                                : point._score >=
                                    60
                                  ? "status-good"
                                  : point._score >=
                                      40
                                    ? "status-fair"
                                    : "status-attention"
                            }
                          />

                          {scoreStatus(
                            point._score
                          )}
                        </span>

                      </div>
                    );
                  }
                )}

            </div>
          )}

        </section>


        <section className="card key-insights-card">

          <div className="progress-section-header compact">

            <div>
              <span className="card-eyebrow">
                KEY INSIGHTS
              </span>

              <h3>
                What your progress means
              </h3>
            </div>

          </div>


          <div className="insight-item">
            <div className="insight-icon">
              ↗
            </div>

            <div>
              <strong>
                {changeFromFirst !== null &&
                changeFromFirst > 0
                  ? "Great progress!"
                  : "Keep building your history"}
              </strong>

              <p>
                {changeFromFirst !== null
                  ? `Your score has ${
                      changeFromFirst >= 0
                        ? "improved"
                        : "changed"
                    } by ${Math.abs(
                      changeFromFirst
                    )} points since your first check-in.`
                  : "More check-ins will make your trend more meaningful."}
              </p>
            </div>
          </div>


          <div className="insight-item">
            <div className="insight-icon">
              ✓
            </div>

            <div>
              <strong>
                Stay consistent
              </strong>

              <p>
                You have completed{" "}
                {completedRoutineSteps} of{" "}
                {routineItems.length} current
                routine steps.
              </p>
            </div>
          </div>


          <div className="insight-item">
            <div className="insight-icon">
              !
            </div>

            <div>
              <strong>
                Focus areas
              </strong>

              <p>
                Continue following your personalized
                routine and monitor changes in your
                skin profile and AI-assisted assessments.
              </p>
            </div>
          </div>

        </section>

      </div>


      <section className="card score-explanation-card">

        <div className="progress-section-header compact">

          <div>
            <span className="card-eyebrow">
              HOW YOUR SKIN SCORE IS CALCULATED
            </span>

            <h3>
              Understand your score
            </h3>
          </div>

        </div>

        <p>
          Your score is a skincare-planning indicator
          based on the factors tracked by the application,
          including skin condition, lifestyle habits,
          sleep, routine consistency and hydration.
        </p>

        <div className="score-factor-grid">

          <div>
            <strong>35%</strong>
            <span>Skin condition</span>
          </div>

          <div>
            <strong>20%</strong>
            <span>Lifestyle habits</span>
          </div>

          <div>
            <strong>15%</strong>
            <span>Sleep</span>
          </div>

          <div>
            <strong>20%</strong>
            <span>Routine consistency</span>
          </div>

          <div>
            <strong>10%</strong>
            <span>Hydration</span>
          </div>

        </div>

        <small>
          This is an AI-assisted skincare indicator,
          not a medical diagnosis.
        </small>

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
  completedRoutine = {},
}) {
  const [exporting, setExporting] = useState("");
  const [exportMessage, setExportMessage] = useState("");

  const normalizeList = (value) => {
    if (Array.isArray(value)) return value;
    if (typeof value === "string") {
      return value
        .split(",")
        .map((item) => item.trim())
        .filter(Boolean);
    }
    return [];
  };

  const displayValue = (value) => {
    if (value === null || value === undefined || value === "") {
      return "Not available";
    }

    if (Array.isArray(value)) {
      return value.length ? value.join(", ") : "None";
    }

    if (typeof value === "object") {
      return Object.entries(value)
        .map(([key, item]) => `${key}: ${displayValue(item)}`)
        .join("; ");
    }

    return String(value);
  };

  const getLatestAnalysis = () => {
    const ai = analysis?.ai_analysis || analysis || {};
    const top = ai?.top_prediction || ai?.primary_concern || {};

    return {
      concern:
        top?.label ||
        ai?.condition ||
        ai?.predicted_condition ||
        ai?.prediction ||
        "No analysis available",
      confidence:
        top?.confidence_percent ??
        ai?.confidence_percent ??
        (top?.confidence != null
          ? Number(top.confidence) * 100
          : null),
      status:
        ai?.analysis_status ||
        "AI-assisted facial skin analysis",
      summary:
        ai?.primary_summary ||
        "No additional AI analysis summary is available.",
      predictions:
        ai?.predictions ||
        ai?.all_predictions ||
        [],
      date:
        analysis?.created_at ||
        analysis?.timestamp ||
        ai?.created_at ||
        null,
    };
  };

  const getProgressPoints = () => {
    return (
      progress?.history ||
      progress?.data ||
      progress?.records ||
      []
    )
      .map((point, index) => ({
        ...point,
        _index: index,
        _score: getNumber(
          point?.score ??
            point?.health_score ??
            point?.skin_score,
          0
        ),
      }))
      .filter((point) => Number.isFinite(point._score))
      .sort((a, b) => {
        const dateA = new Date(
          a?.date ||
            a?.progress_date ||
            a?.created_at ||
            0
        ).getTime();

        const dateB = new Date(
          b?.date ||
            b?.progress_date ||
            b?.created_at ||
            0
        ).getTime();

        if (
          Number.isFinite(dateA) &&
          Number.isFinite(dateB) &&
          dateA !== dateB
        ) {
          return dateA - dateB;
        }

        return a._index - b._index;
      });
  };

  const progressPoints = getProgressPoints();

  const latestProgressScore =
    progress?.current_score ??
    (progressPoints.length
      ? progressPoints[progressPoints.length - 1]._score
      : score);

  const firstProgressScore =
    progressPoints.length
      ? progressPoints[0]._score
      : null;

  const improvement =
    firstProgressScore !== null &&
    latestProgressScore !== null &&
    latestProgressScore !== undefined
      ? Number(
          (
            Number(latestProgressScore) -
            Number(firstProgressScore)
          ).toFixed(1)
        )
      : null;

  const averageProgress =
    progressPoints.length
      ? Number(
          (
            progressPoints.reduce(
              (sum, point) => sum + point._score,
              0
            ) / progressPoints.length
          ).toFixed(1)
        )
      : null;

  const bestProgress =
    progressPoints.length
      ? Math.max(
          ...progressPoints.map(
            (point) => point._score
          )
        )
      : null;

  const routineItems = [
    ...normalizeList(
      routine?.morning ||
        routine?.morning_routine
    ).map((item) => ({
      period: "Morning",
      name:
        typeof item === "object"
          ? item?.name || item?.title || "Skincare step"
          : item,
    })),
    ...normalizeList(
      routine?.evening ||
        routine?.evening_routine
    ).map((item) => ({
      period: "Evening",
      name:
        typeof item === "object"
          ? item?.name || item?.title || "Skincare step"
          : item,
    })),
    ...normalizeList(
      routine?.weekly ||
        routine?.weekly_treatment
    ).map((item) => ({
      period: "Weekly",
      name:
        typeof item === "object"
          ? item?.name || item?.title || "Skincare step"
          : item,
    })),
  ];

  const completedRoutineSteps =
    routineItems.filter(
      (item) => completedRoutine?.[`${item.period}-${routineItems.indexOf(item)}-${item.name}`]
    ).length;

  const routineCompletion =
    routineItems.length > 0
      ? Math.round(
          (completedRoutineSteps /
            routineItems.length) *
            100
        )
      : 0;

  const latestAnalysis = getLatestAnalysis();

  const reportDefinitions = [
    {
      id: "assessment",
      title: "Skin Assessment Report",
      icon: "✦",
      description:
        "Latest AI-assisted facial analysis, possible concerns and confidence.",
    },
    {
      id: "health",
      title: "Skin Health Report",
      icon: "♡",
      description:
        "Current health score, improvement and tracked skincare factors.",
    },
    {
      id: "routine",
      title: "Routine Report",
      icon: "✓",
      description:
        "Your personalized morning, evening and weekly skincare routine.",
    },
    {
      id: "progress",
      title: "Progress Report",
      icon: "↗",
      description:
        "Health-score history, improvement and check-in trends.",
    },
  ];

  function buildRows(type) {
    if (type === "assessment") {
      const rows = [
        ["Report", "Skin Assessment Report"],
        ["Generated", new Date().toLocaleString()],
        ["Possible Primary Concern", latestAnalysis.concern],
        [
          "Confidence",
          latestAnalysis.confidence !== null &&
          latestAnalysis.confidence !== undefined
            ? `${Number(latestAnalysis.confidence).toFixed(1)}%`
            : "Not available",
        ],
        ["Analysis Status", latestAnalysis.status],
        ["Summary", latestAnalysis.summary],
        ["Skin Type", profile?.skin_type || "Not available"],
        ["User Concerns", displayValue(profile?.concerns)],
        ["Allergies", displayValue(profile?.allergies)],
        ["Sensitivities", displayValue(profile?.sensitivities)],
        [
          "Disclaimer",
          "AI-assisted information only; not a medical diagnosis.",
        ],
      ];

      if (latestAnalysis.predictions.length) {
        latestAnalysis.predictions.forEach(
          (prediction, index) => {
            rows.push([
              `Prediction ${index + 1}`,
              `${prediction?.label || "Unknown"} — ${
                prediction?.confidence_percent != null
                  ? Number(
                      prediction.confidence_percent
                    ).toFixed(1) + "%"
                  : "confidence unavailable"
              }`,
            ]);
          }
        );
      }

      return rows;
    }

    if (type === "health") {
      return [
        ["Report", "Skin Health Report"],
        ["Generated", new Date().toLocaleString()],
        ["Current Health Score", `${Number(score || 0).toFixed(1)}/100`],
        ["Average Recorded Score", averageProgress !== null ? `${averageProgress}/100` : "Not available"],
        ["Best Recorded Score", bestProgress !== null ? `${bestProgress}/100` : "Not available"],
        ["Improvement From First Check-in", improvement !== null ? `${improvement > 0 ? "+" : ""}${improvement} points` : "Not available"],
        ["Skin Type", profile?.skin_type || "Not available"],
        ["Age Group", profile?.age_group || "Not available"],
        ["Lifestyle", displayValue(profile?.lifestyle)],
        ["Sleep Quality", profile?.sleep_quality || "Not available"],
        ["Water Intake", profile?.water_intake ? `${profile.water_intake} L/day` : "Not available"],
        ["Environmental Exposure", displayValue(profile?.environmental_exposure)],
        ["Skin Concerns", displayValue(profile?.concerns)],
        ["Routine Steps", routineItems.length],
        ["Routine Completion", `${routineCompletion}%`],
        ["Progress Check-ins", progressPoints.length],
        [
          "Interpretation",
          "The health score is an AI-assisted skincare-planning indicator based on factors tracked by the application.",
        ],
      ];
    }

    if (type === "routine") {
      const rows = [
        ["Report", "Routine Report"],
        ["Generated", new Date().toLocaleString()],
        ["Skin Type", profile?.skin_type || "Not available"],
        ["Skin Concerns", displayValue(profile?.concerns)],
        ["Routine Steps", routineItems.length],
      ];

      if (routineItems.length) {
        routineItems.forEach((item, index) => {
          rows.push([
            `${item.period} Step ${index + 1}`,
            item.name,
          ]);
        });
      } else {
        rows.push([
          "Routine",
          "No routine steps are currently available.",
        ]);
      }

      return rows;
    }

    const rows = [
      ["Report", "Progress Report"],
      ["Generated", new Date().toLocaleString()],
      ["Current Score", latestProgressScore !== null && latestProgressScore !== undefined ? `${Number(latestProgressScore).toFixed(1)}/100` : "Not available"],
      ["First Recorded Score", firstProgressScore !== null ? `${Number(firstProgressScore).toFixed(1)}/100` : "Not available"],
      ["Improvement", improvement !== null ? `${improvement > 0 ? "+" : ""}${improvement} points` : "Not available"],
      ["Average Score", averageProgress !== null ? `${averageProgress}/100` : "Not available"],
      ["Best Score", bestProgress !== null ? `${bestProgress}/100` : "Not available"],
      ["Total Check-ins", progressPoints.length],
      ["Routine Completion", `${routineCompletion}%`],
    ];

    progressPoints.forEach((point, index) => {
      rows.push([
        `Check-in ${index + 1}`,
        `${point?.date || point?.progress_date || point?.created_at || "Recorded"} — ${Number(point._score).toFixed(1)}/100`,
      ]);
    });

    return rows;
  }

  function fileSafeName(type) {
    return `skin-${type}-report`;
  }

  async function exportPdf(type) {
    const key = `${type}-pdf`;
    setExporting(key);
    setExportMessage("");

    try {
      const definition =
        reportDefinitions.find(
          (item) => item.id === type
        );

      const rows = buildRows(type);
      const doc = new jsPDF();

      doc.setFontSize(20);
      doc.text("Skin Intelligence", 20, 22);

      doc.setFontSize(15);
      doc.text(definition?.title || "Skin Report", 20, 32);

      doc.setFontSize(9);
      doc.text(
        `Generated: ${new Date().toLocaleString()}`,
        20,
        40
      );

      let y = 53;

      rows.forEach(([label, value]) => {
        const text = `${label}: ${displayValue(value)}`;
        const wrapped = doc.splitTextToSize(
          text,
          170
        );

        if (y + wrapped.length * 5 > 275) {
          doc.addPage();
          y = 20;
        }

        doc.setFontSize(10);
        doc.text(wrapped, 20, y);
        y += wrapped.length * 5 + 4;
      });

      doc.setFontSize(8);
      doc.text(
        "AI-assisted skincare information only. This report is not a medical diagnosis.",
        20,
        288
      );

      doc.save(
        `${fileSafeName(type)}.pdf`
      );

      setExportMessage(
        `${definition?.title || "Report"} PDF exported successfully.`
      );
    } catch (error) {
      setExportMessage(
        error?.message ||
          "Unable to export the PDF report."
      );
    } finally {
      setExporting("");
    }
  }

  function exportExcel(type) {
    const key = `${type}-excel`;
    setExporting(key);
    setExportMessage("");

    try {
      const definition =
        reportDefinitions.find(
          (item) => item.id === type
        );

      const rows = buildRows(type);

      const worksheet =
        XLSX.utils.aoa_to_sheet([
          ["Skin Intelligence Report"],
          [definition?.title || "Skin Report"],
          [],
          ["Field", "Value"],
          ...rows,
        ]);

      worksheet["!cols"] = [
        { wch: 34 },
        { wch: 90 },
      ];

      const workbook =
        XLSX.utils.book_new();

      XLSX.utils.book_append_sheet(
        workbook,
        worksheet,
        "Report"
      );

      XLSX.writeFile(
        workbook,
        `${fileSafeName(type)}.xlsx`
      );

      setExportMessage(
        `${definition?.title || "Report"} Excel file exported successfully.`
      );
    } catch (error) {
      setExportMessage(
        error?.message ||
          "Unable to export the Excel report."
      );
    } finally {
      setExporting("");
    }
  }

  return (
    <div className="reports-page">
      <PageHeader
        eyebrow="REPORTS & EXPORT"
        title="Skin Reports"
        description="Create downloadable reports from your current skin profile, AI analysis, personalized routine and real progress data."
      />

      <section className="card report-summary-card">
        <div>
          <span className="card-eyebrow">
            LIVE REPORT DATA
          </span>
          <h3>
            Reports use your current application data
          </h3>
          <p>
            Every export is generated from the information
            currently available in your profile, AI analysis,
            routine and progress history.
          </p>
        </div>

        <div className="report-summary-score">
          <span>Current Health Score</span>
          <strong>
            {Number(score || 0).toFixed(1)}
            <small>/100</small>
          </strong>
        </div>
      </section>

      <div className="report-grid">
        {reportDefinitions.map(
          (report) => (
            <div
              className="card report-card report-card-enhanced"
              key={report.id}
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

              <div className="report-data-preview">
                {report.id === "assessment" && (
                  <>
                    <span>Primary concern</span>
                    <strong>
                      {latestAnalysis.concern}
                    </strong>
                  </>
                )}

                {report.id === "health" && (
                  <>
                    <span>Current score</span>
                    <strong>
                      {Number(score || 0).toFixed(1)}/100
                    </strong>
                  </>
                )}

                {report.id === "routine" && (
                  <>
                    <span>Personalized steps</span>
                    <strong>
                      {routineCompletion}%
                    </strong>
                  </>
                )}

                {report.id === "progress" && (
                  <>
                    <span>Recorded check-ins</span>
                    <strong>
                      {progressPoints.length}
                    </strong>
                  </>
                )}
              </div>

              <div className="report-actions">
                <button
                  className="secondary-button"
                  disabled={
                    exporting !== ""
                  }
                  onClick={() =>
                    exportPdf(report.id)
                  }
                >
                  {exporting ===
                  `${report.id}-pdf`
                    ? "Creating PDF..."
                    : "Export PDF"}
                </button>

                <button
                  className="secondary-button"
                  disabled={
                    exporting !== ""
                  }
                  onClick={() =>
                    exportExcel(
                      report.id
                    )
                  }
                >
                  {exporting ===
                  `${report.id}-excel`
                    ? "Creating Excel..."
                    : "Export Excel"}
                </button>
              </div>
            </div>
          )
        )}
      </div>

      {exportMessage && (
        <div className="report-export-message">
          ✓ {exportMessage}
        </div>
      )}

      <section className="card export-note">
        <strong>
          Export Center
        </strong>

        <p>
          PDF and Excel reports are generated directly
          from your current application data. No fixed
          scores, skin concerns or routine values are
          inserted into the exported report.
        </p>

        <small>
          Reports are informational and should not be
          treated as medical diagnosis or medical advice.
        </small>
      </section>
    </div>
  );
}


/* ============================================================
   NOTIFICATIONS
============================================================ */

function NotificationsPage({
  notifications = [],
}) {
  const highPriorityCount =
    notifications.filter(
      (notification) =>
        notification.priority === "high"
    ).length;

  return (
    <div>

      <PageHeader
        eyebrow="LIVE UPDATES"
        title="Notifications"
        description="Personalized reminders and insights generated from your current skin profile, routine, analysis and progress."
      />


      <section className="notification-summary-card">

        <div>
          <span className="notification-summary-label">
            CURRENT UPDATES
          </span>

          <h3>
            {notifications.length} personalized{" "}
            {notifications.length === 1
              ? "notification"
              : "notifications"}
          </h3>

          <p>
            This page refreshes automatically every 30
            seconds while it is open.
          </p>
        </div>

        <div className="notification-summary-count">
          <strong>
            {highPriorityCount}
          </strong>

          <span>
            needs attention
          </span>
        </div>

      </section>


      {notifications.length === 0 ? (
        <EmptyState
          title="No notifications right now"
          description="Your personalized updates will appear here when the system has something useful to tell you."
        />
      ) : (
        <div className="notification-list">

          {notifications.map(
            (notification) => (

              <article
                className={`card notification-card ${
                  notification.priority === "high"
                    ? "notification-card-priority"
                    : ""
                }`}
                key={notification.id}
              >

                <div
                  className={`notification-icon notification-icon-${notification.priority}`}
                >
                  {notification.icon}
                </div>

                <div className="notification-content">

                  <div className="notification-title-row">

                    <strong>
                      {notification.title}
                    </strong>

                    {notification.priority === "high" && (
                      <span className="notification-priority">
                        Attention
                      </span>
                    )}

                  </div>

                  <p>
                    {notification.text}
                  </p>

                  <small>
                    {notification.time}
                  </small>

                </div>

              </article>

            )
          )}

        </div>
      )}


      <section className="notification-info-card">

        <div className="notification-info-icon">
          ✦
        </div>

        <div>
          <strong>
            How these notifications are generated
          </strong>

          <p>
            Updates are based on the data currently
            available in your skin profile, AI analysis,
            personalized routine, routine completion and
            progress history. They are informational and
            are not medical diagnoses.
          </p>
        </div>

      </section>

    </div>
  );
}
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

function RecommendationList({ items = [] }) {
  const list = Array.isArray(items) ? items : [];

  if (!list.length) {
    return (
      <div className="empty-state">
        <div className="empty-state-icon">✦</div>
        <strong>No recommendations yet</strong>
        <p>Complete your skin profile and AI analysis to receive personalized recommendations.</p>
      </div>
    );
  }

  return (
    <div className="recommendation-list">
      {list.slice(0, 6).map((item, index) => {
        const name =
          item?.name ||
          item?.product_name ||
          item?.title ||
          item?.ingredient ||
          item?.label ||
          `Recommendation ${index + 1}`;
        const description =
          item?.description ||
          item?.reason ||
          item?.benefit ||
          item?.message ||
          "Recommended based on your current skincare information.";
        const suitability =
          item?.suitability ?? item?.match_score ?? item?.score;

        return (
          <div className="recommendation-item" key={`${name}-${index}`}>
            <div className="recommendation-item-icon">✦</div>
            <div className="recommendation-item-content">
              <strong>{String(name)}</strong>
              <p>{String(description)}</p>
            </div>
            {suitability !== undefined && suitability !== null && (
              <span className="recommendation-item-score">
                {Number(suitability).toFixed(0)}%
              </span>
            )}
          </div>
        );
      })}
    </div>
  );
}


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