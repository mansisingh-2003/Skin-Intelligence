"""
AI Skin Analyzer

Uses a skin-condition image classification model to generate
AI-assisted predictions from an uploaded image.

Important:
This is an AI-assisted classification system and is NOT a
medical diagnosis.
"""

from typing import Any, Dict, List

from PIL import Image
from transformers import pipeline


# ============================================================
# MODEL CONFIGURATION
# ============================================================

MODEL_NAME = "LaurianeMD/vit-skin-disease"


# ============================================================
# LOAD MODEL
# ============================================================

print("Loading skin AI model...")

skin_classifier = pipeline(
    "image-classification",
    model=MODEL_NAME
)

print("Skin AI model loaded successfully.")


# ============================================================
# ANALYZE IMAGE
# ============================================================

def analyze_with_ai(
    image_path: str,
    top_k: int = 5
) -> Dict[str, Any]:
    """
    Analyze an image using the skin-condition classifier.

    Parameters
    ----------
    image_path : str
        Path to the uploaded image.

    top_k : int
        Number of predictions to return.

    Returns
    -------
    dict
        Structured AI analysis result.
    """

    # --------------------------------------------------------
    # Open image
    # --------------------------------------------------------

    try:

        image = Image.open(image_path)

        # Make sure the image is fully loaded
        image.load()

    except Exception as e:

        raise ValueError(
            f"Unable to open skin image: {str(e)}"
        )

    # --------------------------------------------------------
    # Convert image to RGB
    # --------------------------------------------------------

    if image.mode != "RGB":

        image = image.convert("RGB")

    # --------------------------------------------------------
    # Run model
    # --------------------------------------------------------

    predictions: List[Dict[str, Any]] = (
        skin_classifier(
            image,
            top_k=top_k
        )
    )

    # --------------------------------------------------------
    # Format predictions
    # --------------------------------------------------------

    formatted_predictions = []

    for prediction in predictions:

        label = prediction.get(
            "label",
            "Unknown"
        )

        score = float(
            prediction.get(
                "score",
                0.0
            )
        )

        formatted_predictions.append(
            {
                "label": label,
                "confidence": round(
                    score,
                    4
                ),
                "confidence_percent": round(
                    score * 100,
                    2
                )
            }
        )

    # --------------------------------------------------------
    # Highest-confidence prediction
    # --------------------------------------------------------

    top_prediction = None

    if formatted_predictions:

        top_prediction = (
            formatted_predictions[0]
        )

    # --------------------------------------------------------
    # Return structured result
    # --------------------------------------------------------

    return {

        "model": MODEL_NAME,

        "analysis_available": True,

        "top_prediction": top_prediction,

        "predictions": formatted_predictions,

        "disclaimer": (
            "This is an AI-assisted skin-condition "
            "classification and is not a medical diagnosis. "
            "Consult a qualified healthcare professional "
            "for medical evaluation."
        )
    }