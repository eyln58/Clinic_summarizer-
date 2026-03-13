"""
nodes/critic.py — Critic Node

Bu node'un görevi:
1. Generator'ın ürettiği taslağı (draft) al
2. Üç kritere göre değerlendir:
   - Açık teşhis koyuyor mu?
   - Klinik ton profesyonel mi?
   - Halüsinasyon var mı?
3. LLM'den STRUCTURED JSON çıktı al: {"approved": bool, "feedback": str}
4. Pydantic ile parse et ve doğrula

Öğrenilen Kavramlar:
- Pydantic BaseModel: LLM çıktısını type-safe yapıya dönüştürme
- JSON mode prompt mühendisliği: LLM'yi JSON döndürmeye yönlendirme
- json.loads() ile string → dict dönüşümü
- LangGraph node'undan state güncellemesi
"""

import os
import json
from dotenv import load_dotenv
from litellm import completion
from pydantic import BaseModel
from state import AgentState

load_dotenv()


# ─────────────────────────────────────────────
# Pydantic Model: LLM'den beklediğimiz yapı
# ─────────────────────────────────────────────
class CriticOutput(BaseModel):
    """
    Critic'in LLM'den döndürmesini beklediğimiz yapı.
    Pydantic otomatik olarak type validation yapar.
    """
    approved: bool      # True = onaylandı, False = reddedildi
    feedback: str       # Reddedilince açıklama, onaylanınca boş string


# ─────────────────────────────────────────────
# Critic Node Fonksiyonu
# ─────────────────────────────────────────────
def critic_node(state: AgentState) -> dict:
    """
    Critic Node: Generator'ın taslağını değerlendirir.
    
    Args:
        state: Mevcut graph state'i (draft içeriyor)
        
    Returns:
        dict: approved ve feedback alanları güncellendi
    """
    
    draft = state["draft"]
    patient_input = state["patient_input"]
    iteration = state.get("iteration", 0)

    print(f"\n{'='*50}")
    print(f"🔍 CRITIC değerlendiriyor... (İterasyon: {iteration})")
    print(f"{'='*50}")

    system_prompt = """Sen bir klinik kalite güvence uzmanısın.
Sana bir klinik özet taslağı verilecek. Aşağıdaki kriterlere göre değerlendir:

1. TIBBİ OLMAYAN İÇERİK: Orijinal hasta semptomu gerçekten sağlık/tıbbi bir şikayet mi? Yoksa alakasız bir metin mi (örn: "i hate you")? Eğer tıbbi bir girdi DEĞİLSE ve taslak olarak tıbbi özet üretilmeye çalışılmışsa REDDET. Ancak girdi tıbbi değilse ve taslakta zaten "Bu girdi tıbbi şikayet içermemektedir" gibi uygun bir uyarı yazılmışsa ONAYLA (çünkü sistemin doğru tepkisidir).
2. TEŞHİS YASAĞI: Taslak kesin teşhis koyuyor mu? (koyuyorsa REDDET)
3. KLİNİK TON: Dil profesyonel ve klinik mi? (değilse REDDET)
4. HALÜSİNASYON: Hasta verisinde olmayan bilgi uyduruluyor mu? (uyduruyorsa REDDET)
5. UYDURMA TERMİNOLOJİ: "morningafter sendromu" gibi tıp literatüründe var olmayan uydurma sendromlar veya "extreme", "complaint" gibi yarı İngilizce kelimeler kullanılmış mı? (kullanılmışsa REDDET ve hedef dildeki tıbbi karşılığını kullanmasını söyle)
6. DİL TUTARLILIĞI (ÇOK ÖNEMLİ): "ORİJİNAL HASTA SEMPTOMU" metni HANGİ DİLDE yazılmışsa, "Değerlendirilecek Klinik Özet Taslağı" da KESİNLİKLE O DİLDE yazılmış olmalıdır. Eğer orijinal metin İngilizce ama taslak Türkçe (veya tam tersi) yazılmışsa ANINDA REDDET ve "Lütfen orijinal girdi ile aynı dilde yazın" de.

ÖNEMLİ KURAL:
Feedback metninde bir alıntı yapacaksan KESİNLİKLE çift tırnak (") kullanma, onun yerine tek tırnak (') kullan. JSON formatını bozmamalısın.

SADECE aşağıdaki JSON formatında yanıt ver, başka hiçbir şey yazma:
{
  "approved": true veya false,
  "feedback": "Eğer reddettiysen NEDEN reddettiğini ve nasıl düzeltilmesi gerektiğini açıkla. Onayladıysan boş string yaz."
}"""

    user_prompt = f"""ORİJİNAL HASTA SEMPTOMU (Asla dışına çıkılamaz, ekstra detay eklenemez):
{patient_input}

Değerlendirilecek Klinik Özet Taslağı:
{draft}

JSON formatında değerlendirmeni yap:"""

    response = completion(
        model="groq/llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        api_key=os.getenv("GROQ_API_KEY"),
    )

    raw_output = response.choices[0].message.content.strip()
    print(f"\n🤖 Critic'in ham yanıtı:\n{raw_output}\n")

    # ── JSON Parse + Pydantic Validation ──
    # LLM bazen ```json ... ``` bloğu içinde dönebildiği için temizle
    cleaned = raw_output
    if "```" in cleaned:
        cleaned = cleaned.split("```")[1]
        if cleaned.startswith("json"):
            cleaned = cleaned[4:]
    cleaned = cleaned.strip()

    # json.loads() içindeki satır sonları ('\n') ve satırbaşı ('\r') karakterlerini temizle 
    # çünkü LLM bazen JSON value'sunun tam ortasında satır atlayabiliyor
    cleaned = cleaned.replace('\n', ' ').replace('\r', '')

    # 1. json.loads ile string → dict
    try:
        parsed_dict = json.loads(cleaned)
    except json.JSONDecodeError as e:
        print(f"\n⚠️ JSON Parse Hatası! Kurtarılmaya çalışılıyor...\nHata: {e}\nHam Veri: {cleaned}")
        # LLM'in json string'i çok bozuksa en basit şekilde fallback yap:
        parsed_dict = {
            "approved": False,
            "feedback": f"JSON parse hatası nedeniyle otomatik reddedildi. Ham LLM çıktısı: {cleaned}"
        }
    
    # 2. Pydantic ile doğrula (type checking + alan kontrolü)
    critic_output = CriticOutput(**parsed_dict)

    if critic_output.approved:
        print("✅ ONAYLANDI! Taslak kabul edildi.")
    else:
        print(f"❌ REDDEDİLDİ!\n   Sebep: {critic_output.feedback}")

    return {
        "approved": critic_output.approved,
        "feedback": critic_output.feedback,
    }
