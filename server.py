import asyncio
import json
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from graph import build_graph
from state import AgentState

app = FastAPI(title="Pneumatic Agent API")

# React Frontend ile iletişim kurabilmek için CORS izinleri
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Graph'ı bir kez oluşturuyoruz (stateless olarak hizmet verecek)
graph = build_graph()

class SummarizeRequest(BaseModel):
    symptom: str

async def event_generator(symptom: str):
    """
    LangGraph üzerinden dönen her adımı SSE (Server-Sent Events) olarak yayınlar.
    Frontend bu sayede kapsülün Generator'da mı yoksa Critic'te mi olduğunu bilir.
    """
    initial_state = AgentState(
        patient_input=symptom,
        draft="",
        feedback="",
        approved=False,
        iteration=0
    )
    
    # 1. Başlangıç Etkileşimi
    yield f"data: {json.dumps({'event': 'START', 'data': 'Starting the pneumatic tube...'})}\n\n"
    
    try:
        # 2. Graph'ın stream API'si ile çalıştırılması 
        # (graph.stream her node bitişinde yield yapar)
        for output in graph.stream(initial_state):
            # output dict formatında döner: {'generator': {'draft': '...', 'iteration': 1}}
            for node_name, state_update in output.items():
                print(f"--- Node: {node_name} tamamlandı ---")
                
                # Bu olayı (node ismini ve son durumu) frontend'e JSON formatında fırlatıyoruz
                event_data = {
                    "event": "NODE_UPDATE",
                    "node": node_name,
                    "state": state_update 
                }
                yield f"data: {json.dumps(event_data)}\n\n"
                
                # Pnömatik tüp hissini artırmak için frontend animasyonuna çok ufak bir zaman tanıyalım
                await asyncio.sleep(0.5)
                
        # 3. Graph Bittiğinde (Critic onayladığında veya 5. iterasyona ulaşıldığında)
        yield f"data: {json.dumps({'event': 'END', 'data': 'Process complete.'})}\n\n"
        
    except Exception as e:
        yield f"data: {json.dumps({'event': 'ERROR', 'data': str(e)})}\n\n"


@app.post("/stream")
async def stream_summary(request: SummarizeRequest):
    """
    React Frontend'in bağlanacağı asıl uç nokta.
    Gelen isteğe göre bir event stream (SSE) açar.
    """
    return StreamingResponse(
        event_generator(request.symptom), 
        media_type="text/event-stream"
    )

if __name__ == "__main__":
    import uvicorn
    # Terminalden çalıştırmak için: python server.py
    uvicorn.run(app, host="0.0.0.0", port=8000)
