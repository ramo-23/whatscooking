import re

STOPWORDS = {
    "of", "and", "the", "a", "an", "in", "with", "to", "for", "into",
    "kg", "g", "ml", "l", "oz", "lb", "lbs", "tsp", "tbsp", "cup", "cups",
    "pcs", "pc", "large", "small", "medium", "fresh", "chopped", "sliced",
    "diced", "minced", "cooked", "raw", "peeled", "ground",
}


def normalize_ingredient_name(name: str) -> str:
    """
    Normalizes ingredient names for consistent storage and matching.
    """
    name = name.strip().lower()
    name = re.sub(r"\s+", " ", name)
    return name


def _singularize(word: str) -> str:
    if word.endswith("es") and len(word) > 4:
        return word[:-2]
    if word.endswith("s") and not word.endswith("ss") and len(word) > 3:
        return word[:-1]
    return word


def tokenize_ingredient(name: str) -> set[str]:
    """
    Breaks an ingredient name into meaningful, singularized tokens,
    stripping units, quantities, and filler words. Used for word-level
    matching rather than fragile whole-string comparison.
    e.g. "chicken weighing 2.3kg" -> {"chicken", "weighing"}
         "chicken breast" -> {"chicken", "breast"}
         shared token "chicken" -> match
    """
    name = normalize_ingredient_name(name)
    raw_tokens = re.findall(r"[a-z]+", name)  # drops numbers/units like "2.3kg" entirely

    tokens = set()
    for word in raw_tokens:
        if word in STOPWORDS or len(word) < 3:
            continue
        tokens.add(_singularize(word))

    return tokens