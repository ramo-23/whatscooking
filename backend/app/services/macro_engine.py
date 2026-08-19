ACTIVITY_MULTIPLIERS = {
    "sedentary": 1.2,
    "light": 1.375,
    "moderate": 1.55,
    "active": 1.725,
    "very_active": 1.9,
}

GOAL_CALORIE_OFFSET = {
    "bulk": 1.15,
    "cut": 0.80,
    "maintain": 1.0,
}

MACRO_SPLITS = {
    "bulk": {"protein": 0.30, "carbs": 0.45, "fat": 0.25},
    "cut": {"protein": 0.40, "carbs": 0.30, "fat": 0.30},
    "maintain": {"protein": 0.30, "carbs": 0.40, "fat": 0.30},
}

PROTEIN_PER_KG = {
    "bulk": 1.8,
    "cut": 2.4,
    "maintain": 1.8,
}

FAT_PER_KG = {
    "bulk": 1.0,
    "cut": 0.8,
    "maintain": 1.0,
}

MIN_DAILY = {
    "calories": {"male": 1500, "female": 1200},
    "protein_g": 50,
    "carbs_g": 130,
    "fat_g": 30,
}


def calculate_bmr(weight_kg: float, height_cm: float, age: int, sex: str) -> float:
    """Mifflin-St Jeor equation."""
    base = (10 * weight_kg) + (6.25 * height_cm) - (5 * age)
    return base + 5 if sex == "male" else base - 161


def calculate_targets(
        weight_kg: float, height_cm: float, age: int, sex: str,
        activity_level: str, goal: str,
) -> dict:
    # Input validation
    if weight_kg <= 0:
        raise ValueError(f"Weight must be positive, got {weight_kg}")
    if height_cm <= 0:
        raise ValueError(f"Height must be positive, got {height_cm}")
    if age < 18 or age > 120:
        raise ValueError(f"Age must be between 18-120, got {age}")
    if sex not in ["male", "female"]:
        raise ValueError(f"Sex must be 'male' or 'female', got {sex}")
    if activity_level not in ACTIVITY_MULTIPLIERS:
        raise ValueError(f"Invalid activity_level: {activity_level}")
    if goal not in GOAL_CALORIE_OFFSET:
        raise ValueError(f"Invalid goal: {goal}")

    # Calculate base calories
    bmr = calculate_bmr(weight_kg, height_cm, age, sex)
    tdee = bmr * ACTIVITY_MULTIPLIERS[activity_level]
    target_calories = round(tdee * GOAL_CALORIE_OFFSET[goal])

    # Enforce minimum calorie intake
    min_calories = MIN_DAILY["calories"][sex]
    max_calories = 4000 if sex == "male" else 3000
    target_calories = max(min_calories, min(target_calories, max_calories))

    # Calculate macros using percentage-based splits (original approach)
    split = MACRO_SPLITS[goal]
    target_protein_g = round((target_calories * split["protein"]) / 4)
    target_carbs_g = round((target_calories * split["carbs"]) / 4)
    target_fat_g = round((target_calories * split["fat"]) / 9)

    # Edge case: Enforce minimums
    target_protein_g = max(MIN_DAILY["protein_g"], target_protein_g)
    target_carbs_g = max(MIN_DAILY["carbs_g"], target_carbs_g)
    target_fat_g = max(MIN_DAILY["fat_g"], target_fat_g)

    # Edge case: Cap protein/fat for extreme bodyweights
    max_protein_g = round(weight_kg * 3.5)
    target_protein_g = min(target_protein_g, max_protein_g)
    
    max_fat_g = round(weight_kg * 2.0)
    target_fat_g = min(target_fat_g, max_fat_g)

    return {
        "target_calories": target_calories,
        "target_protein_g": target_protein_g,
        "target_carbs_g": target_carbs_g,
        "target_fat_g": target_fat_g,
        "protein_percent": round((target_protein_g * 4 / target_calories) * 100, 1),
        "carbs_percent": round((target_carbs_g * 4 / target_calories) * 100, 1),
        "fat_percent": round((target_fat_g * 9 / target_calories) * 100, 1),
    }