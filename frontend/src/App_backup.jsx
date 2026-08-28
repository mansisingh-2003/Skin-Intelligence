import { useState } from "react";
import "./App.css";

const API_URL = "http://127.0.0.1:8000";

function App() {
  const [backendStatus, setBackendStatus] = useState("");
  const [token, setToken] = useState("");
  const [file, setFile] = useState(null);
  const [uploadStatus, setUploadStatus] = useState("");
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  // =========================================================
  // 1. TEST BACKEND CONNECTION
  // =========================================================
  const testBackend = async () => {
    setBackendStatus("Testing...");
    setError("");

    try {
      const response = await fetch(`${API_URL}/`);
      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          data.detail || `Backend returned status ${response.status}`
        );
      }

      setBackendStatus(
        `Backend connected successfully: ${JSON.stringify(data)}`
      );
    } catch (err) {
      setBackendStatus("");
      setError(
        err.message ||
          "Unable to connect to the backend. Make sure FastAPI is running."
      );
    }
  };

  // =========================================================
  // 2. UPLOAD IMAGE AND RUN AI ANALYSIS
  // =========================================================
  const uploadImage = async () => {
    setError("");
    setUploadStatus("");
    setResult(null);

    // Check token
    if (!token.trim()) {
      setError("Please enter your JWT token first.");
      return;
    }

    // Check image
    if (!file) {
      setError("Please select a skin image first.");
      return;
    }

    setLoading(true);
    setUploadStatus("Uploading image and running AI analysis...");

    const formData = new FormData();
    formData.append("file", file);

    try {
      const response = await fetch(`${API_URL}/skin-analysis/upload`, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token.trim()}`,
        },
        body: formData,
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          data.detail ||
            data.message ||
            `Analysis failed with status ${response.status}`
        );
      }

      setResult(data);
      setUploadStatus("AI analysis completed successfully.");
    } catch (err) {
      setUploadStatus("");
      setError(err.message || "Something went wrong during analysis.");
    } finally {
      setLoading(false);
    }
  };

  // =========================================================
  // 3. HANDLE FILE SELECTION
  // =========================================================
  const handleFileChange = (event) => {
    const selectedFile = event.target.files?.[0];

    setError("");
    setUploadStatus("");
    setResult(null);

    if (!selectedFile) {
      setFile(null);
      return;
    }

    if (!selectedFile.type.startsWith("image/")) {
      setError("Please select a valid image file.");
      setFile(null);
      return;
    }

    setFile(selectedFile);
  };

  // =========================================================
  // 4. CLEAR EVERYTHING
  // =========================================================
  const clearAll = () => {
    setBackendStatus("");
    setToken("");
    setFile(null);
    setUploadStatus("");
    setResult(null);
    setError("");

    const fileInput = document.getElementById("skin-image");

    if (fileInput) {
      fileInput.value = "";
    }
  };

  // =========================================================
  // 5. GET AI ANALYSIS OBJECT
  // =========================================================
  const aiAnalysis = result?.ai_analysis || result?.analysis || result;

  const topPrediction = aiAnalysis?.top_prediction;

  const predictions = Array.isArray(aiAnalysis?.predictions)
    ? aiAnalysis.predictions
    : [];

  // =========================================================
  // 6. MAIN UI
  // =========================================================
  return (
    <div
      style={{
        minHeight: "100vh",
        background:
          "linear-gradient(135deg, #f0fdf4 0%, #eff6ff 50%, #f8fafc 100%)",
        padding: "30px 20px",
        boxSizing: "border-box",
        fontFamily:
          "Inter, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
      }}
    >
      <div
        style={{
          maxWidth: "900px",
          margin: "0 auto",
          background: "white",
          borderRadius: "20px",
          padding: "35px",
          boxShadow: "0 10px 40px rgba(0, 0, 0, 0.08)",
        }}
      >
        {/* =================================================
            HEADER
        ================================================== */}
        <div
          style={{
            textAlign: "center",
            marginBottom: "35px",
          }}
        >
          <div
            style={{
              fontSize: "48px",
              marginBottom: "10px",
            }}
          >
            🧴
          </div>

          <h1
            style={{
              margin: 0,
              fontSize: "38px",
              color: "#111827",
              fontWeight: "700",
            }}
          >
            Skin Intelligence
          </h1>

          <p
            style={{
              marginTop: "8px",
              color: "#6b7280",
              fontSize: "16px",
            }}
          >
            AI-Assisted Skin Condition Analysis
          </p>
        </div>

        {/* =================================================
            ERROR MESSAGE
        ================================================== */}
        {error && (
          <div
            style={{
              background: "#fef2f2",
              border: "1px solid #fecaca",
              color: "#b91c1c",
              padding: "15px 18px",
              borderRadius: "10px",
              marginBottom: "20px",
              fontSize: "14px",
            }}
          >
            ❌ {error}
          </div>
        )}

        {/* =================================================
            STEP 1 - BACKEND CONNECTION
        ================================================== */}
        <section
          style={{
            background: "#f8fafc",
            border: "1px solid #e5e7eb",
            borderRadius: "14px",
            padding: "25px",
            marginBottom: "20px",
          }}
        >
          <h2
            style={{
              marginTop: 0,
              color: "#111827",
              fontSize: "20px",
            }}
          >
            1. Backend Connection
          </h2>

          <p
            style={{
              color: "#6b7280",
              fontSize: "14px",
            }}
          >
            First check whether the FastAPI backend is running.
          </p>

          <button
            type="button"
            onClick={testBackend}
            style={{
              background: "#2563eb",
              color: "white",
              border: "none",
              borderRadius: "8px",
              padding: "12px 24px",
              cursor: "pointer",
              fontSize: "15px",
              fontWeight: "600",
            }}
          >
            Test Backend
          </button>

          {backendStatus && (
            <div
              style={{
                marginTop: "18px",
                padding: "14px",
                background: "#ecfdf5",
                border: "1px solid #bbf7d0",
                color: "#15803d",
                borderRadius: "8px",
                fontSize: "14px",
                wordBreak: "break-word",
              }}
            >
              ✅ {backendStatus}
            </div>
          )}
        </section>

        {/* =================================================
            STEP 2 - JWT TOKEN
        ================================================== */}
        <section
          style={{
            background: "#f8fafc",
            border: "1px solid #e5e7eb",
            borderRadius: "14px",
            padding: "25px",
            marginBottom: "20px",
          }}
        >
          <h2
            style={{
              marginTop: 0,
              color: "#111827",
              fontSize: "20px",
            }}
          >
            2. Authorization
          </h2>

          <p
            style={{
              color: "#6b7280",
              fontSize: "14px",
              marginBottom: "15px",
            }}
          >
            Paste the JWT token obtained from Swagger's{" "}
            <b>Authorize</b> button.
          </p>

          <input
            type="password"
            value={token}
            onChange={(e) => setToken(e.target.value)}
            placeholder="Paste JWT token here"
            style={{
              width: "100%",
              boxSizing: "border-box",
              padding: "13px 15px",
              borderRadius: "8px",
              border: "1px solid #d1d5db",
              fontSize: "14px",
              outline: "none",
            }}
          />

          <p
            style={{
              marginTop: "10px",
              color: "#6b7280",
              fontSize: "12px",
            }}
          >
            Do not include the word "Bearer". Paste only the token.
          </p>

          {token && (
            <div
              style={{
                marginTop: "10px",
                color: "#15803d",
                fontSize: "13px",
              }}
            >
              ✅ JWT token entered
            </div>
          )}
        </section>

        {/* =================================================
            STEP 3 - UPLOAD IMAGE
        ================================================== */}
        <section
          style={{
            background: "#f8fafc",
            border: "1px solid #e5e7eb",
            borderRadius: "14px",
            padding: "25px",
            marginBottom: "20px",
          }}
        >
          <h2
            style={{
              marginTop: 0,
              color: "#111827",
              fontSize: "20px",
            }}
          >
            3. Upload Skin Image
          </h2>

          <p
            style={{
              color: "#6b7280",
              fontSize: "14px",
            }}
          >
            Select an image and send it to the AI analysis backend.
          </p>

          <input
            id="skin-image"
            type="file"
            accept="image/*"
            onChange={handleFileChange}
            style={{
              marginTop: "10px",
              marginBottom: "15px",
              width: "100%",
            }}
          />

          {file && (
            <div
              style={{
                background: "#eff6ff",
                border: "1px solid #bfdbfe",
                padding: "13px",
                borderRadius: "8px",
                marginBottom: "15px",
                color: "#1d4ed8",
                fontSize: "14px",
              }}
            >
              📷 <b>Selected file:</b> {file.name}
            </div>
          )}

          <button
            type="button"
            onClick={uploadImage}
            disabled={loading}
            style={{
              background: loading ? "#9ca3af" : "#16a34a",
              color: "white",
              border: "none",
              borderRadius: "8px",
              padding: "13px 28px",
              cursor: loading ? "not-allowed" : "pointer",
              fontSize: "15px",
              fontWeight: "600",
            }}
          >
            {loading ? "Analyzing..." : "Analyze Skin Image"}
          </button>

          {uploadStatus && (
            <div
              style={{
                marginTop: "18px",
                padding: "14px",
                background: "#ecfdf5",
                border: "1px solid #bbf7d0",
                color: "#15803d",
                borderRadius: "8px",
                fontSize: "14px",
              }}
            >
              {loading ? "⏳ " : "✅ "}
              {uploadStatus}
            </div>
          )}
        </section>

        {/* =================================================
            STEP 4 - AI RESULT
        ================================================== */}
        {result && (
          <section
            style={{
              background: "#f0fdf4",
              border: "1px solid #bbf7d0",
              borderRadius: "14px",
              padding: "25px",
              marginBottom: "20px",
            }}
          >
            <h2
              style={{
                marginTop: 0,
                color: "#166534",
                textAlign: "center",
              }}
            >
              4. AI Analysis Result
            </h2>

            {/* TOP PREDICTION */}
            {topPrediction && (
              <div
                style={{
                  background: "white",
                  borderRadius: "12px",
                  padding: "25px",
                  marginTop: "20px",
                  textAlign: "center",
                  boxShadow: "0 4px 15px rgba(0,0,0,0.05)",
                }}
              >
                <div
                  style={{
                    fontSize: "14px",
                    color: "#6b7280",
                    marginBottom: "8px",
                  }}
                >
                  DETECTED CONDITION
                </div>

                <div
                  style={{
                    fontSize: "28px",
                    fontWeight: "700",
                    color: "#111827",
                    marginBottom: "20px",
                  }}
                >
                  {topPrediction.label || "Unknown"}
                </div>

                <div
                  style={{
                    fontSize: "14px",
                    color: "#6b7280",
                    marginBottom: "8px",
                  }}
                >
                  CONFIDENCE
                </div>

                <div
                  style={{
                    fontSize: "36px",
                    fontWeight: "700",
                    color: "#16a34a",
                  }}
                >
                  {topPrediction.confidence_percent ??
                    (topPrediction.confidence
                      ? Math.round(topPrediction.confidence * 100)
                      : 0)}
                  %
                </div>
              </div>
            )}

            {/* ALL PREDICTIONS */}
            {predictions.length > 0 && (
              <div
                style={{
                  marginTop: "25px",
                }}
              >
                <h3
                  style={{
                    color: "#111827",
                    marginBottom: "12px",
                  }}
                >
                  All Predictions
                </h3>

                {predictions.map((prediction, index) => {
                  const confidence =
                    prediction.confidence_percent ??
                    (prediction.confidence
                      ? Math.round(prediction.confidence * 100)
                      : 0);

                  return (
                    <div
                      key={index}
                      style={{
                        display: "flex",
                        justifyContent: "space-between",
                        alignItems: "center",
                        background: "white",
                        padding: "14px 16px",
                        borderRadius: "8px",
                        marginBottom: "8px",
                        border: "1px solid #e5e7eb",
                      }}
                    >
                      <span
                        style={{
                          color: "#374151",
                          fontWeight: "500",
                        }}
                      >
                        {prediction.label || "Unknown"}
                      </span>

                      <b
                        style={{
                          color: "#16a34a",
                        }}
                      >
                        {confidence}%
                      </b>
                    </div>
                  );
                })}
              </div>
            )}

            {/* ANALYSIS INFORMATION */}
            <div
              style={{
                background: "white",
                borderRadius: "10px",
                padding: "18px",
                marginTop: "20px",
                fontSize: "14px",
                color: "#374151",
              }}
            >
              {result.analysis_id && (
                <p>
                  <b>Analysis ID:</b> {result.analysis_id}
                </p>
              )}

              {result.user_id && (
                <p>
                  <b>User ID:</b> {result.user_id}
                </p>
              )}

              {aiAnalysis?.model && (
                <p>
                  <b>AI Model:</b> {aiAnalysis.model}
                </p>
              )}
            </div>

            {/* DISCLAIMER */}
            {result.disclaimer && (
              <div
                style={{
                  marginTop: "20px",
                  padding: "15px",
                  background: "#fff7ed",
                  border: "1px solid #fed7aa",
                  borderRadius: "8px",
                  color: "#9a3412",
                  fontSize: "13px",
                }}
              >
                ⚠️ <b>Disclaimer:</b> {result.disclaimer}
              </div>
            )}

            {aiAnalysis?.disclaimer && !result.disclaimer && (
              <div
                style={{
                  marginTop: "20px",
                  padding: "15px",
                  background: "#fff7ed",
                  border: "1px solid #fed7aa",
                  borderRadius: "8px",
                  color: "#9a3412",
                  fontSize: "13px",
                }}
              >
                ⚠️ <b>Disclaimer:</b> {aiAnalysis.disclaimer}
              </div>
            )}

            {/* RAW BACKEND RESPONSE */}
            <details
              style={{
                marginTop: "25px",
                background: "#f8fafc",
                padding: "14px",
                borderRadius: "10px",
                border: "1px solid #e5e7eb",
              }}
            >
              <summary
                style={{
                  cursor: "pointer",
                  fontWeight: "600",
                  color: "#374151",
                }}
              >
                View complete backend response
              </summary>

              <pre
                style={{
                  marginTop: "15px",
                  whiteSpace: "pre-wrap",
                  wordBreak: "break-word",
                  fontSize: "12px",
                  color: "#374151",
                  background: "white",
                  padding: "15px",
                  borderRadius: "8px",
                  overflowX: "auto",
                }}
              >
                {JSON.stringify(result, null, 2)}
              </pre>
            </details>
          </section>
        )}

        {/* =================================================
            CLEAR BUTTON
        ================================================== */}
        {(token || file || result || error || backendStatus) && (
          <div
            style={{
              textAlign: "center",
              marginTop: "20px",
            }}
          >
            <button
              type="button"
              onClick={clearAll}
              style={{
                background: "#6b7280",
                color: "white",
                border: "none",
                borderRadius: "8px",
                padding: "11px 28px",
                cursor: "pointer",
                fontSize: "14px",
              }}
            >
              Clear
            </button>
          </div>
        )}

        {/* =================================================
            FOOTER
        ================================================== */}
        <div
          style={{
            marginTop: "30px",
            paddingTop: "20px",
            borderTop: "1px solid #e5e7eb",
            textAlign: "center",
            fontSize: "13px",
            color: "#9ca3af",
          }}
        >
          Skin Intelligence • AI-Assisted Skin Condition Analysis
        </div>
      </div>
    </div>
  );
}

export default App;