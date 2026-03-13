import re


TURKISH_CHARS = set("çğıöşüÇĞİÖŞÜ")
TURKISH_HINTS = {
    "bir",
    "ve",
    "ile",
    "hasta",
    "şikayet",
    "ağrı",
    "baş",
    "olduğunu",
    "belirtti",
    "için",
    "olarak",
    "değerlendirme",
}
ENGLISH_HINTS = {
    "the",
    "and",
    "with",
    "patient",
    "reports",
    "report",
    "has",
    "have",
    "headache",
    "pain",
    "for",
    "days",
    "symptoms",
}


def _tokenize(text: str) -> list[str]:
    return re.findall(r"[A-Za-zÇĞİÖŞÜçğıöşü']+", text.lower())


def detect_language(text: str) -> str:
    if any(char in TURKISH_CHARS for char in text):
        return "tr"

    tokens = _tokenize(text)
    turkish_score = sum(token in TURKISH_HINTS for token in tokens)
    english_score = sum(token in ENGLISH_HINTS for token in tokens)

    if turkish_score > english_score:
        return "tr"

    return "en"


def language_name(language_code: str) -> str:
    return "Turkish" if language_code == "tr" else "English"


def is_language_match(source_text: str, generated_text: str) -> bool:
    expected = detect_language(source_text)
    actual = detect_language(generated_text)
    return expected == actual
