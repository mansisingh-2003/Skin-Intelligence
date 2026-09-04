"""
AI Facial Skin Analyzer

This module provides AI-assisted analysis of facial images
for common visible skincare concerns.

Model:
    SopanhaZinII/facial-condition-model

Supported concerns:
    - Acne
    - Dry Skin
    - Oily Skin
    - Dark Spots
    - Wrinkles

Important:
This system is NOT a medical diagnostic system.
Results represent possible visible skincare concerns only.
"""

from typing import Any, Dict, List

import numpy as np
from PIL import Image
import tensorflow as tf

from huggingface_hub import hf_hub_download


# ============================================================
# MODEL CONFIGURATION
# ============================================================

MODEL_REPOSITORY = "SopanhaZinII/facial-condition-model"
MODEL_FILENAME = "finetuned_best.h5"

IMAGE_SIZE = (224, 224)

SKIN_CONCERNS = [
    "Acne",
    "Dry Skin",
    "Oily Skin",
    "Dark Spots",
    "Wrinkles",
]

# We use a moderate threshold so that weak predictions
# are not presented as meaningful concerns.
DETECTION_THRESHOLD = 0.50


# ============================================================
# GLOBAL MODEL
# ============================================================

skin_model = None


# ============================================================
# MODEL LOADING
# ============================================================

def load_skin_model():
    """
    Load the facial skin model once.

    Hugging Face automatically caches the downloaded model,
    so subsequent application starts do not need to download
    the file again.
    """

    global skin_model

    if skin_model is not None:
        return skin_model

    print("Loading facial skin analysis model...")

    model_path = hf_hub_download(
        repo_id=MODEL_REPOSITORY,
        filename=MODEL_FILENAME,
    )

    skin_model = tf.keras.models.load_model(
        model_path,
        compile=False,
    )

    print("Facial skin analysis model loaded successfully.")

    return skin_model


# ============================================================
# IMAGE VALIDATION
# ============================================================

def validate_image(image: Image.Image) -> None:
    """
    Perform basic validation before sending an image
    to the AI model.
    """

    width, height = image.size

    if width < 100 or height < 100:
        raise ValueError(
            "The uploaded image is too small. "
            "Please upload a clearer face image."
        )

    if width > 10000 or height > 10000:
        raise ValueError(
            "The uploaded image is unusually large. "
            "Please choose a normal-sized image."
        )


# ============================================================
# IMAGE PREPARATION
# ============================================================

def prepare_image(image_path: str) -> np.ndarray:
    """
    Convert the uploaded image into the format expected
    by the facial skin model.

    Expected model input:
        224 x 224 x 3 RGB
    """

    try:
        image = Image.open(image_path)
        image.load()
    except Exception as exc:
        raise ValueError(
            f"Unable to open the uploaded image: {str(exc)}"
        ) from exc

    validate_image(image)

    if image.mode != "RGB":
        image = image.convert("RGB")

    image = image.resize(
        IMAGE_SIZE,
        Image.Resampling.LANCZOS,
    )

    image_array = np.asarray(
        image,
        dtype=np.float32,
    )

    image_array = np.expand_dims(
        image_array,
        axis=0,
    )

    return image_array


# ============================================================
# OUTPUT NORMALIZATION
# ============================================================

def normalize_predictions(
    raw_prediction: Any,
) -> List[float]:
    """
    Convert the model output into five safe probabilities.
    """

    prediction = np.asarray(
        raw_prediction,
        dtype=np.float32,
    )

    if prediction.ndim == 2:
        prediction = prediction[0]

    prediction = prediction.flatten()

    if len(prediction) != len(SKIN_CONCERNS):
        raise ValueError(
            "Unexpected model output size. "
            f"Expected {len(SKIN_CONCERNS)} predictions, "
            f"received {len(prediction)}."
        )

    # The model uses sigmoid outputs.
    # This safety conversion handles logits if encountered.
    if np.any(prediction < 0.0) or np.any(prediction > 1.0):
        prediction = 1.0 / (
            1.0 + np.exp(-prediction)
        )

    prediction = np.clip(
        prediction,
        0.0,
        1.0,
    )

    return prediction.tolist()


# ============================================================
# PREDICTION FORMATTER
# ============================================================

def format_prediction(
    label: str,
    confidence: float,
) -> Dict[str, Any]:
    """
    Create a frontend-friendly prediction object.
    """

    confidence = float(confidence)

    return {
        "label": label,
        "confidence": round(
            confidence,
            4,
        ),
        "confidence_percent": round(
            confidence * 100,
            2,
        ),
    }


# ============================================================
# MAIN AI ANALYSIS
# ============================================================

def analyze_with_ai(
    image_path: str,
    top_k: int = 5,
) -> Dict[str, Any]:
    """
    Analyze an uploaded facial image.

    The result contains:
        - primary possible concern
        - all model predictions
        - meaningful detected concerns
        - analysis status
        - model information
        - disclaimer
    """

    model = load_skin_model()

    image_array = prepare_image(
        image_path
    )

    # --------------------------------------------------------
    # MODEL PREDICTION
    # --------------------------------------------------------

    raw_prediction = model.predict(
        image_array,
        verbose=0,
    )

    probabilities = normalize_predictions(
        raw_prediction
    )

    # --------------------------------------------------------
    # CREATE PREDICTIONS
    # --------------------------------------------------------

    predictions: List[Dict[str, Any]] = []

    for label, probability in zip(
        SKIN_CONCERNS,
        probabilities,
    ):
        predictions.append(
            format_prediction(
                label,
                probability,
            )
        )

    # Highest confidence first.
    predictions.sort(
        key=lambda item: item["confidence"],
        reverse=True,
    )

    # --------------------------------------------------------
    # TOP K
    # --------------------------------------------------------

    try:
        requested_top_k = int(top_k)
    except (TypeError, ValueError):
        requested_top_k = 5

    requested_top_k = max(
        1,
        min(
            requested_top_k,
            len(predictions),
        ),
    )

    top_predictions = predictions[
        :requested_top_k
    ]

    # --------------------------------------------------------
    # MEANINGFUL CONCERNS
    # --------------------------------------------------------

    detected_concerns = [
        prediction
        for prediction in predictions
        if prediction["confidence"] >= DETECTION_THRESHOLD
    ]

    # --------------------------------------------------------
    # PRIMARY CONCERN
    # --------------------------------------------------------

    primary_concern = None

    if detected_concerns:
        primary_concern = detected_concerns[0]

    # --------------------------------------------------------
    # ANALYSIS STATUS
    # --------------------------------------------------------

    if primary_concern:

        analysis_status = (
            "Possible visible skin concern detected."
        )

    else:

        analysis_status = (
            "No sufficiently confident skin concern "
            "was detected from this image."
        )

    # --------------------------------------------------------
    # HUMAN-READABLE SUMMARY
    # --------------------------------------------------------

    if primary_concern:

        primary_summary = (
            f"The analysis suggests "
            f"{primary_concern['label'].lower()} "
            "may be a visible skincare concern."
        )

    else:

        primary_summary = (
            "The image did not produce a sufficiently "
            "confident skincare concern."
        )

    # --------------------------------------------------------
    # FINAL RESULT
    # --------------------------------------------------------

    return {

        "model": MODEL_REPOSITORY,

        "analysis_available": True,

        "primary_concern": primary_concern,

        # Kept for compatibility with the existing frontend.
        "top_prediction": primary_concern,

        "predictions": top_predictions,

        "detected_concerns": detected_concerns,

        "analysis_status": analysis_status,

        "primary_summary": primary_summary,

        "confidence_threshold_percent": (
            DETECTION_THRESHOLD * 100
        ),

        "input_size": "224x224 RGB",

        "disclaimer": (
            "This is an AI-assisted facial skin analysis "
            "for possible visible skincare concerns. "
            "It is not a medical diagnosis. Results may "
            "be affected by lighting, camera quality, "
            "image angle, makeup, image quality, and "
            "other factors. Consult a qualified healthcare "
            "professional for medical evaluation."
        ),
    }