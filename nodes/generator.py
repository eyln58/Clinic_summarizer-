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

    # System prompt: Modele rolünü tanımlıyoruz (Sistem dilini İngilizce yapıyoruz ki her dile uyum sağlasın)
    system_prompt = """You are an experienced clinical documentation specialist.
You evaluate patient symptoms and prepare a professional clinical summary draft.

YOUR RULES:
- DO NOT make a definitive diagnosis — only summarize the symptoms and observations.
- Use clinical and professional language.
- Do not hallucinate or invent information not present in the input.
- Keep the summary brief. If the input is 1 sentence, reply with 1 sentence. Do not force yourself to write an essay.
- CRITICAL LANGUAGE RULE: You MUST output the clinical summary in the EXACT SAME LANGUAGE as the patient's input. If the input is English, output English. If Turkish, output Turkish.
- Output ONLY the clinical summary. Do not use conversational filler, greetings, or explanations like "Here is your summary".
"""

    # User prompt: Hasta verisini ve feedback'i gönderiyoruz
    # Burası da İngilizce olmak zorunda, aksi halde model kafası karışır
    user_prompt = f"""Patient Symptom Input:
{patient_input}

{feedback_section}
Please write a clinical summary draft based on the symptoms above."""

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

    print(f"\n📝 Üretilen Taslak:\n{draft}\n")

    # Sadece değişen alanları döndür
    # iteration: 1 döndürülüyor → operator.add reducer ile mevcut değere eklenir
    return {
        "draft": draft,
        "iteration": 1,
    }
