"""
graph.py — LangGraph Graph Tanımı

Bu dosyada tüm parçaları bir araya getiriyoruz:
1. StateGraph oluştur
2. Node'ları ekle (add_node)
3. Edge'leri bağla (add_edge)
4. Conditional edge ile döngüyü kur (add_conditional_edges)
5. Graph'ı compile et

Öğrenilen Kavramlar:
- StateGraph: LangGraph'ın ana graph sınıfı
- add_node(): node'u graph'a kayıt et
- add_edge(): iki node arasında sabit bağlantı
- add_conditional_edges(): runtime'da yön belirle (routing)
- set_entry_point(): graph nerede başlar?
- compile(): graph'ı çalışmaya hazır hale getir
- END: LangGraph'ın özel bitiş noktası
"""

from langgraph.graph import StateGraph, END
from state import AgentState
from nodes.generator import generator_node
from nodes.critic import critic_node


# ─────────────────────────────────────────────
# Conditional Edge Fonksiyonu (Router)
# ─────────────────────────────────────────────
def route_after_critic(state: AgentState) -> str:
    """
    Critic'in kararına göre bir sonraki adımı belirler.
    
    Bu fonksiyon LangGraph tarafından her Critic çalışmasından
    sonra çağrılır. String döndürür:
    - "generator" → döngü devam eder, Generator tekrar çalışır
    - END          → graph biter, son sonuç döner
    
    Args:
        state: Güncel graph state'i
        
    Returns:
        str: Bir sonraki node'un adı veya END
    """
    approved = state.get("approved", False)
    iteration = state.get("iteration", 0)

    if approved:
        print(f"\n🎉 Onaylandı! {iteration}. iterasyonda tamamlandı.")
        return END
    
    if iteration >= 5:
        print(f"\n⚠️  Maksimum iterasyona ({iteration}) ulaşıldı. Döngü durduruluyor.")
        return END
    
    print(f"\n🔄 Reddet → Generator'a geri gönderiliyor. (İterasyon: {iteration})")
    return "generator"


# ─────────────────────────────────────────────
# Graph Kurulumu
# ─────────────────────────────────────────────
def build_graph():
    """
    Reflection Loop graph'ını oluşturur ve compile eder.
    
    Akış:
        [START] → generator → critic → (route) → generator (döngü)
                                              ↓
                                           [END]
    """
    
    # 1. Graph'ı oluştur — hangi state kullanacağını söyle
    graph = StateGraph(AgentState)

    # 2. Node'ları ekle (isim → fonksiyon)
    graph.add_node("generator", generator_node)
    graph.add_node("critic", critic_node)

    # 3. Başlangıç noktasını belirle
    graph.set_entry_point("generator")

    # 4. Generator → Critic arasında sabit edge (her zaman Critic'e gider)
    graph.add_edge("generator", "critic")

    # 5. Critic'ten sonra conditional edge (runtime'da karar ver)
    graph.add_conditional_edges(
        "critic",           # kaynak node
        route_after_critic, # routing fonksiyonu
        {
            "generator": "generator",  # fonksiyon "generator" döndürürse
            END: END,                  # fonksiyon END döndürürse
        }
    )

    # 6. Compile et → çalışmaya hazır graph objesi döner
    compiled = graph.compile()
    
    return compiled
