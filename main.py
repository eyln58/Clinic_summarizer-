"""
main.py — Reflection Loop CLI

Tüm sistemi bir araya getirir:
- Kullanıcıdan hasta semptomunu alır
- Graph'ı çalıştırır (generator → critic → loop)
- Her iterasyonu ekrana basar
- Final onaylı özeti gösterir

Öğrenilen Kavramlar:
- graph.invoke(): graph'ı başlatmak ve çalıştırmak
- Initial state: graph'a verilen başlangıç verisi
- Final state: graph'ın döndürdüğü son state
"""

from graph import build_graph

def main():
    print("\n" + "="*60)
    print("   🏥  Klinik Özet Üretici — Reflection Loop Agent")
    print("="*60)
    print("\nBu sistem hasta semptomlarını alarak profesyonel bir")
    print("klinik özet üretir ve kalite kontrolden geçirir.\n")
    
    # Kullanıcıdan girdi al
    patient_input = input("Hasta semptomlarını girin: ").strip()
    
    if not patient_input:
        print("❌ Semptom girişi boş olamaz.")
        return

    print("\n" + "─"*60)
    print("⚙️  Graph başlatılıyor...")
    print("─"*60)

    # Graph'ı oluştur
    graph = build_graph()

    # Başlangıç state'ini hazırla
    initial_state = {
        "patient_input": patient_input,
        "draft": "",
        "feedback": "",
        "approved": False,
        "iteration": 0,
    }

    # Graph'ı çalıştır — tüm döngü burada oluyor!
    # invoke() graph tamamlanana kadar bekler ve final state'i döner
    final_state = graph.invoke(initial_state)

    # Sonucu göster
    print("\n" + "="*60)
    print("📋  SONUÇ")
    print("="*60)
    print(f"\n✅ Onay Durumu : {'Onaylandı' if final_state['approved'] else 'Limit doldu (5 iterasyon)'}")
    print(f"🔢 Toplam İterasyon: {final_state['iteration']}")
    print(f"\n📄 Final Klinik Özet:\n")
    print(final_state["draft"])
    print("\n" + "="*60)


if __name__ == "__main__":
    main()
