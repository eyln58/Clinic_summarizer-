"""
test_critic.py — Critic Node'u test et

2 senaryo test ediyoruz:
1. Kötü taslak → Critic reddetmeli
2. İyi taslak → Critic onaylamalı
"""

from state import AgentState
from nodes.critic import critic_node

print("\n" + "="*60)
print("TEST 1: Teşhis içeren (kötü) taslak — REDDEDİLMELİ")
print("="*60)

bad_state: AgentState = {
    "patient_input": "Hasta baş ağrısı ve ateş yaşıyor.",
    "draft": "Hastanın semptomları incelendiğinde grip tanısı konulmuştur. Hasta grip hastalığına yakalanmıştır.",
    "feedback": "",
    "approved": False,
    "iteration": 1,
}

result1 = critic_node(bad_state)
print(f"\nSonuç → approved: {result1['approved']}")


print("\n" + "="*60)
print("TEST 2: Profesyonel klinik taslak — ONANMALI")
print("="*60)

good_state: AgentState = {
    "patient_input": "Hasta baş ağrısı ve ateş yaşıyor.",
    "draft": "Hasta, 3 gün süredir şiddetli baş ağrısı ve 38°C ateş şikayetiyle başvurmuştur. Semptomlar viral veya bakteriyel etkenlerle uyumlu olabilir. Daha kapsamlı değerlendirme için ek tetkik önerilmektedir.",
    "feedback": "",
    "approved": False,
    "iteration": 1,
}

result2 = critic_node(good_state)
print(f"\nSonuç → approved: {result2['approved']}")
