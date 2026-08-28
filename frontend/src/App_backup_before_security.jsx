import { useEffect, useState } from "react";
import "./App.css";

const API_URL = "http://127.0.0.1:8000";

function App() {
  // ============================================================
  // STATE
  // ============================================================

  const [backendStatus, setBackendStatus] = useState("");
  const [token, setToken] = useState("");

  const [file, setFile] = useState(null);
  const [previewUrl, setPreviewUrl] = useState("");

  const [uploadStatus, setUploadStatus] = useState("");
  const [result, setResult] = useState(null);

  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  // ============================================================
  // CLEANUP IMAGE PREVIEW URL
  // ============================================================

  useEffect(() => {
    return () => {
      if (previewUrl) {
        URL.revokeObjectURL(previewUrl);
      }
    };
  }, [previewUrl]);

  // ============================================================
  // 1. TEST BACKEND
  // ============================================================

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
        `✅ Backend connected successfully: ${JSON.stringify(data)}`
      );
    } catch (err) {
      setBackendStatus("");
      setError(
        `Unable to connect to backend. Make sure FastAPI is running. ${err.message}`
      );
    }
  };

  // ============================================================
  // 2. TOKEN CHANGE
  // ============================================================

  const handleTokenChange = (event) => {
    setToken(event.target.value);
    setError("");
  };

  // ============================================================
  // 3. IMAGE SELECTION
  // ============================================================

  const handleFileChange = (event) => {
    const selectedFile = event.target.files?.[0];

    setError("");
    setUploadStatus("");
    setResult(null);

    if (!selectedFile) {
      setFile(null);
      setPreviewUrl("");
      return;
    }

    // Check that the selected file is an image
    if (!selectedFile.type.startsWith("image/")) {
      setFile(null);
      setPreviewUrl("");
      setError("Please select a valid image file.");
      return;
    }

    // Remove previous preview URL
    if (previewUrl) {
      URL.revokeObjectURL(previewUrl);
    }

    // Save selected file
    setFile(selectedFile);

    // Create preview
    const newPreviewUrl = URL.createObjectURL(selectedFile);
    setPreviewUrl(newPreviewUrl);
  };

  // ============================================================
  // 4. ANALYZE SKIN IMAGE
  // ============================================================

  const analyzeSkin = async () => {
    setError("");
    setUploadStatus("");
    setResult(null);

    // Check token
    if (!token.trim()) {
      setError("Please enter your JWT token before analyzing the image.");
      return;
    }

    // Check image
    if (!file) {
      setError("Please choose a skin image first.");
      return;
    }

    setLoading(true);
    setUploadStatus("Uploading image and running AI analysis...");

    try {
      const formData = new FormData();

      // IMPORTANT:
      // FastAPI UploadFile parameter is expected as "file".
      formData.append("file", file);

      const response = await fetch(`${API_URL}/skin-analysis/upload`, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token.trim()}`,
        },
        body: formData,
      });

      let data = {};

      try {
        data = await response.json();
      } catch {
        data = {};
      }

      console.log("AI ANALYSIS RESPONSE:", data);

      if (!response.ok) {
        const backendError =
          data.detail ||
          data.message ||
          `Server returned status ${response.status}`;

        throw new Error(backendError);
      }

      setResult(data);

      setUploadStatus("✅ AI analysis completed successfully.");
    } catch (err) {
      console.error("AI ANALYSIS ERROR:", err);

      setUploadStatus("");
      setError(err.message || "Something went wrong during analysis.");
    } finally {
      setLoading(false);
    }
  };

  // ============================================================
  // 5. CLEAR EVERYTHING
  // ============================================================

  const clearAll = () => {
    setBackendStatus("");
    setToken("");
    setFile(null);
    setUploadStatus("");
    setResult(null);
    setError("");
    setLoading(false);

    if (previewUrl) {
      URL.revokeObjectURL(previewUrl);
    }

    setPreviewUrl("");

    // Reset file input
    const fileInput = document.getElementById("skin-image-input");

    if (fileInput) {
      fileInput.value = "";
    }
  };

  // ============================================================
  // HELPER FUNCTIONS
  // ============================================================

  const getAIAnalysis = () => {
    return result?.ai_analysis || {};
  };

  const getTopPrediction = () => {
    return getAIAnalysis()?.top_prediction || {};
  };

  const getPredictions = () => {
    return getAIAnalysis()?.predictions || [];
  };

  const topPrediction = getTopPrediction();

  const predictions = getPredictions();

  const conditionName =
    topPrediction?.label ||
    topPrediction?.condition ||
    topPrediction?.name ||
    "Unknown";

  const confidence =
    topPrediction?.confidence_percent ??
    (topPrediction?.confidence != null
      ? Number(topPrediction.confidence) * 100
      : null);

  const modelName =
    getAIAnalysis()?.model ||
    result?.model ||
    "AI Skin Analysis Model";

  const analysisId =
    result?.analysis_id ??
    result?.analysisId ??
    getAIAnalysis()?.analysis_id ??
    "N/A";

  const userId = result?.user_id ?? result?.userId ?? "N/A";

  const disclaimer =
    result?.disclaimer ||
    "This is an AI-assisted skin-condition classification and is not a medical diagnosis. Consult a qualified healthcare professional for medical evaluation.";

  // ============================================================
  // UI
  // ============================================================

  return (
    <div className="app">
      <div className="container">

        {/* ======================================================
            HEADER
        ====================================================== */}

        <header className="header">
          <div className="header-icon">🔬</div>

          <h1>Skin Intelligence</h1>

          <p>
            AI-Assisted Skin
            <br />
            Condition Analysis
          </p>
        </header>

        {/* ======================================================
            1. BACKEND CONNECTION
        ====================================================== */}

        <section className="card">
          <div className="step-number">1</div>

          <h2>Backend Connection</h2>

          <p className="description">
            First check whether the FastAPI backend is running.
          </p>

          <button
            className="primary-button"
            onClick={testBackend}
            disabled={loading}
          >
            Test Backend
          </button>

          {backendStatus && (
            <div className="success-message">
              {backendStatus}
            </div>
          )}
        </section>

        {/* ======================================================
            2. AUTHORIZATION
        ====================================================== */}

        <section className="card">
          <div className="step-number">2</div>

          <h2>Authorization</h2>

          <p className="description">
            Paste the JWT token obtained from Swagger's{" "}
            <strong>Authorize</strong> button.
          </p>

          <input
            type="password"
            value={token}
            onChange={handleTokenChange}
            placeholder="Paste JWT token here"
            className="token-input"
          />

          <p className="small-text">
            Do not include the word "Bearer". Paste only the token.
          </p>

          {token.trim() && (
            <div className="token-success">
              ✅ JWT token entered
            </div>
          )}
        </section>

        {/* ======================================================
            3. UPLOAD SKIN IMAGE
        ====================================================== */}

        <section className="card">
          <div className="step-number">3</div>

          <h2>Upload Skin Image</h2>

          <p className="description">
            Select a clear, sufficiently high-resolution image and
            send it to the AI analysis backend.
          </p>

          <input
            id="skin-image-input"
            type="file"
            accept="image/*"
            onChange={handleFileChange}
            className="file-input"
          />

          {/* ====================================================
              IMAGE PREVIEW
          ==================================================== */}

          {previewUrl && file && (
            <div className="preview-container">

              <h3>Image Preview</h3>

              <div className="image-preview-wrapper">
                <img
                  src={previewUrl}
                  alt="Selected skin preview"
                  className="image-preview"
                />
              </div>

              <p className="preview-note">
                Please make sure the image is clear and the skin
                area is visible before analysis.
              </p>
            </div>
          )}

          {/* ====================================================
              SELECTED FILE
          ==================================================== */}

          {file && (
            <div className="selected-file">
              📷 <strong>Selected file:</strong> {file.name}
            </div>
          )}

          {/* ====================================================
              ANALYZE BUTTON
          ==================================================== */}

          <button
            className="analyze-button"
            onClick={analyzeSkin}
            disabled={loading || !file || !token.trim()}
          >
            {loading ? "Analyzing..." : "Analyze Skin Image"}
          </button>

          {/* ====================================================
              UPLOAD STATUS
          ==================================================== */}

          {uploadStatus && (
            <div className="upload-success">
              {uploadStatus}
            </div>
          )}
        </section>

        {/* ======================================================
            ERROR
        ====================================================== */}

        {error && (
          <section className="error-box">
            <div className="error-title">
              ⚠️ Analysis Error
            </div>

            <div className="error-message">
              {error}
            </div>
          </section>
        )}

        {/* ======================================================
            4. AI ANALYSIS RESULT
        ====================================================== */}

        {result && (
          <section className="result-card">

            <h2>4. AI Analysis Result</h2>

            {/* ==================================================
                MAIN RESULT
            ================================================== */}

            <div className="main-result">

              <div className="result-label">
                DETECTED CONDITION
              </div>

              <div className="condition-name">
                {conditionName}
              </div>

              <div className="result-label confidence-label">
                CONFIDENCE
              </div>

              <div className="confidence">
                {confidence !== null
                  ? `${Number(confidence).toFixed(2)}%`
                  : "N/A"}
              </div>
            </div>

            {/* ==================================================
                CONFIDENCE BAR
            ================================================== */}

            {confidence !== null && (
              <div className="confidence-section">

                <div className="confidence-header">
                  <span>Confidence Score</span>

                  <strong>
                    {Number(confidence).toFixed(2)}%
                  </strong>
                </div>

                <div className="confidence-bar">
                  <div
                    className="confidence-fill"
                    style={{
                      width: `${Math.min(
                        Math.max(Number(confidence), 0),
                        100
                      )}%`,
                    }}
                  />
                </div>
              </div>
            )}

            {/* ==================================================
                ALL PREDICTIONS
            ================================================== */}

            {predictions.length > 0 && (
              <div className="predictions-section">

                <h3>All Predictions</h3>

                {predictions.map((prediction, index) => {

                  const predictionConfidence =
                    prediction?.confidence_percent ??
                    (prediction?.confidence != null
                      ? Number(prediction.confidence) * 100
                      : 0);

                  const predictionLabel =
                    prediction?.label ||
                    prediction?.condition ||
                    prediction?.name ||
                    "Unknown";

                  return (
                    <div
                      className="prediction-item"
                      key={`${predictionLabel}-${index}`}
                    >

                      <div className="prediction-top">

                        <span className="prediction-label">
                          {predictionLabel}
                        </span>

                        <span className="prediction-value">
                          {Number(
                            predictionConfidence
                          ).toFixed(2)}
                          %
                        </span>

                      </div>

                      <div className="prediction-bar">
                        <div
                          className="prediction-fill"
                          style={{
                            width: `${Math.min(
                              Math.max(
                                Number(
                                  predictionConfidence
                                ),
                                0
                              ),
                              100
                            )}%`,
                          }}
                        />
                      </div>

                    </div>
                  );
                })}
              </div>
            )}

            {/* ==================================================
                ANALYSIS INFORMATION
            ================================================== */}

            <div className="analysis-info">

              <div>
                <strong>Analysis ID:</strong>{" "}
                {analysisId}
              </div>

              <div>
                <strong>User ID:</strong>{" "}
                {userId}
              </div>

              <div>
                <strong>AI Model:</strong>{" "}
                {modelName}
              </div>

            </div>

            {/* ==================================================
                DISCLAIMER
            ================================================== */}

            <div className="disclaimer">
              ⚠️ <strong>Disclaimer:</strong>{" "}
              {disclaimer}
            </div>

            {/* ==================================================
                COMPLETE BACKEND RESPONSE
            ================================================== */}

            <details className="backend-details">

              <summary>
                View complete backend response
              </summary>

              <pre>
                {JSON.stringify(result, null, 2)}
              </pre>

            </details>

          </section>
        )}

        {/* ======================================================
            CLEAR BUTTON
        ====================================================== */}

        {(token || file || result || error) && (
          <div className="clear-container">

            <button
              type="button"
              onClick={clearAll}
              className="clear-button"
            >
              Clear
            </button>

          </div>
        )}

        {/* ======================================================
            FOOTER
        ====================================================== */}

        <footer>
          Skin Intelligence • AI-Assisted Skin
          Condition Analysis
        </footer>

      </div>
    </div>
  );
}

export default App;