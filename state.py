"""
state.py — LangGraph State Tanımı

Bu dosya, tüm graph boyunca akan ortak veri yapısını tanımlar.
Her node bu state'i okur ve günceller.

Öğrenilen Kavramlar:
- TypedDict: Python type-safe dictionary
- Annotated + operator.add: LangGraph'ta "reducer" — 
  paralel nodlar aynı alana yazarken nasıl birleştirilir?
  operator.add ile int alanlar toplanır (+=)
"""

from typing import TypedDict, Annotated
import operator


class AgentState(TypedDict):
    # Kullanıcıdan gelen hasta semptomu — hiç değişmez
    patient_input: str

    # Generator'ın ürettiği klinik özet taslağı
    draft: str

    # Critic'in verdiği geri bildirim (reddedince)
    feedback: str

    # Critic'in kararı: True = onaylandı, False = reddedildi
    approved: bool

    # Kaç kez döngü çalıştı?
    # Annotated[int, operator.add] → reducer demek:
    # Her node 1 ekleyince LangGraph bunları toplar
    iteration: Annotated[int, operator.add]
