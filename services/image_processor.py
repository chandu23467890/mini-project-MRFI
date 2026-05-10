from io import BytesIO

from PIL import Image, ImageStat


class ImageProcessor:
    @staticmethod
    def analyze_food_image(file_storage):
        image = Image.open(BytesIO(file_storage.read()))
        image = image.convert("RGB")
        width, height = image.size
        stat = ImageStat.Stat(image.resize((128, 128)))
        brightness = sum(stat.mean) / 3
        color_variance = sum(stat.var) / 3

        portion_factor = min(2.0, max(0.6, (width * height) / 500000))
        density_factor = 0.8 if brightness > 150 else 1.1
        complexity_factor = 1.2 if color_variance > 1500 else 0.9
        estimated_carbs = round(28 * portion_factor * density_factor * complexity_factor)

        return {
            "estimated_carbs_grams": max(5, min(160, estimated_carbs)),
            "confidence": "LOW",
            "analysis_notes": "Image-based carbohydrate estimate should be confirmed manually.",
        }
