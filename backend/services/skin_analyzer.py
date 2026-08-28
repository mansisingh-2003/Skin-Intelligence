from PIL import Image
import os


def analyze_skin_image(image_path: str):
    """
    Basic skin image analysis service.

    This is the initial analysis layer of the project.
    It validates the image and extracts basic image characteristics.

    A trained skin-analysis model can be plugged into this service later.
    """

    # ---------------------------------------------------------
    # 1. Check whether image exists
    # ---------------------------------------------------------

    if not os.path.exists(image_path):
        raise FileNotFoundError(
            f"Skin image not found: {image_path}"
        )

    # ---------------------------------------------------------
    # 2. Open image
    # ---------------------------------------------------------

    image = Image.open(image_path)

    # Make sure image is actually loaded
    image.load()

    # ---------------------------------------------------------
    # 3. Basic image information
    # ---------------------------------------------------------

    width, height = image.size

    image_format = image.format
    image_mode = image.mode

    # ---------------------------------------------------------
    # 4. Basic validation
    # ---------------------------------------------------------

    if width < 200 or height < 200:
        return {
            "status": "error",
            "message": "Image resolution is too low for skin analysis.",
            "image_width": width,
            "image_height": height
        }

    # ---------------------------------------------------------
    # 5. Calculate image quality information
    # ---------------------------------------------------------

    total_pixels = width * height

    # ---------------------------------------------------------
    # 6. Initial analysis structure
    #
    # These values are placeholders for the actual trained
    # skin-analysis model that we will connect next.
    # ---------------------------------------------------------

    analysis = {
        "status": "success",

        "image": {
            "width": width,
            "height": height,
            "format": image_format,
            "mode": image_mode,
            "pixels": total_pixels
        },

        "skin_concerns": {
            "acne": False,
            "pigmentation": False,
            "dryness": False,
            "sensitivity": False,
            "dark_circles": False,
            "wrinkles": False,
            "redness": False
        },

        "confidence": {
            "acne": 0.0,
            "pigmentation": 0.0,
            "dryness": 0.0,
            "sensitivity": 0.0,
            "dark_circles": 0.0,
            "wrinkles": 0.0,
            "redness": 0.0
        },

        "message": (
            "Image validated successfully. "
            "AI skin analysis model is ready to be connected."
        )
    }

    return analysis