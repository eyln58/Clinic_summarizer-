"""
nodes/generator.py — Generator Node

Bu node'un görevi:
1. Hasta semptomlarını (patient_input) al
2. Varsa Critic'ten gelen feedback'i al
3. Groq API'ye (LiteLLM üzerinden) prompt gönder
4. Klinik özet taslağı (draft) üret ve state'e kaydet

Öğrenilen Kavramlar:
- LangGraph node'u: state alır, dict döner (güncellenen alanlar)
- LiteLLM: completion() fonksiyonu ile LLM çağrısı
- System prompt + user prompt yapısı
- State'ten veri okuma ve güncelleme
"""

import os
from dotenv import load_dotenv
from litellm import completion
from state import AgentState
from language_utils import detect_language, language_name, is_language_match

# .env dosyasından API key'i yükle
load_dotenv()


def generator_node(state: AgentState) -> dict:
    """
    Generator Node: Hasta semptomlarından klinik özet taslağı üretir.
    
    Args:
        state: Mevcut graph state'i
        
    Returns:
        dict: Güncellenen state alanları (sadece değişenler)
    """
    
    patient_input = state["patient_input"]
    feedback = state.get("feedback", "")
    iteration = state.get("iteration", 0)
    expected_language = detect_language(patient_input)

    print(f"\n{'='*50}")
    print(f"🖊️  GENERATOR çalışıyor... (İterasyon: {iteration + 1})")
    print(f"{'='*50}")

    # Feedback varsa, bunu da prompt'a ekle
    feedback_section = ""
    if feedback:
        feedback_section = f"""
Önceki taslak reddedildi. Critic'in geri bildirimi:
{feedback}

Bu geri bildirimi dikkate alarak taslağı düzelt.
"""

    # System prompt: modeli gerçekten klinik özet formatına zorlarız.
    system_prompt = """You are an experienced clinical documentation specialist.
You convert raw patient symptom descriptions into a concise clinical summary.

YOUR RULES:
- MEDICAL CONTENT ONLY: If the patient input is clearly NOT related to health, medical conditions, or symptoms (for example insults, random chat, or statements like 'i hate you'), DO NOT summarize it. Instead, output a warning message in the original input's language.
- DO NOT make a definitive diagnosis. Only summarize reported symptoms and relevant observations.
- Use concise, professional, clinical wording.
- Do not hallucinate or invent information not present in the input.
- Keep the summary brief. Usually 1 sentence is enough.
- CRITICAL LANGUAGE RULE: Output the summary in the EXACT SAME LANGUAGE as the patient's input.
- IMPORTANT STYLE RULE: Do NOT simply copy the patient's wording with small grammar fixes. Transform colloquial or first-person wording into a short clinical summary.
- Prefer formulations like 'Patient reports...' / 'Hasta ... şikayeti bildirmektedir.' in the same language as the input.
- Output ONLY the final clinical summary. No greetings, labels, or explanations.
"""

    # User prompt: Hasta verisini ve feedback'i gönderiyoruz
    # Burası da İngilizce olmak zorunda, aksi halde model kafası karışır
    user_prompt = f"""Target output language: {language_name(expected_language)}

Patient Symptom Input:
{patient_input}

{feedback_section}
Write one short professional clinical summary based on the symptoms above.
Do not merely correct spelling. Rewrite the content in clinical summary style."""

    # LiteLLM üzerinden Groq API çağrısı
    # Model adı: "groq/llama-3.3-70b-versatile"
    response = completion(
        model="groq/llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        api_key=os.getenv("GROQ_API_KEY"),
    )

    # LLM'den gelen metni çıkar
    draft = response.choices[0].message.content.strip()

    if not is_language_match(patient_input, draft):
        print(
            f"\n⚠️ Language mismatch detected. Expected {language_name(expected_language)}, retrying generator response."
        )
        repair_prompt = f"""Rewrite the following clinical summary in {language_name(expected_language)}.

Rules:
- Keep exactly the same medical meaning.
- Do not add new facts.
- Output only the corrected summary.

Original patient input:
{patient_input}

Draft to rewrite:
{draft}
"""
        repair_response = completion(
            model="groq/llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "system",
                    "content": "You fix language mismatches in clinical summaries while preserving meaning exactly.",
                },
                {"role": "user", "content": repair_prompt},
            ],
            api_key=os.getenv("GROQ_API_KEY"),
        )
        repaired_draft = repair_response.choices[0].message.content.strip()
        if is_language_match(patient_input, repaired_draft):
            draft = repaired_draft

    print(f"\n📝 Üretilen Taslak:\n{draft}\n")

    # Sadece değişen alanları döndür
    # iteration: 1 döndürülüyor → operator.add reducer ile mevcut değere eklenir
    return {
        "draft": draft,
        "iteration": 1,
    }
