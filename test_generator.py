"""
test_generator.py — Generator Node'u test et

Bu script: generator_node'u doğrudan çağırarak
LLM'den gerçek bir yanıt alınıp alınmadığını doğrular.
"""

from state import AgentState
from nodes.generator import generator_node

# Test state'i oluştur
test_state: AgentState = {
    "patient_input": "Hasta son 3 gündür şiddetli baş ağrısı, ateş (38.5°C) ve boğaz ağrısı yaşıyor. Öksürük de mevcut.",
    "draft": "",
    "feedback": "",
    "approved": False,
    "iteration": 0,
}

# Generator node'u çalıştır
result = generator_node(test_state)

print("\n✅ Generator node başarıyla çalıştı!")
print(f"Döndürülen alanlar: {list(result.keys())}")
print(f"İterasyon artışı: +{result['iteration']}")
