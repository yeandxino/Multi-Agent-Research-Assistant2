from fastapi import FastAPI
from pydantic import BaseModel
import uvicorn
from fastapi.middleware.cors import CORSMiddleware
from study_assistant import agent,memory
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
class ChatRequest(BaseModel):
    message:str
class ChatResponse(BaseModel):
    reply:str

@app.post("/chat", response_model=ChatResponse)
async def chat(request:ChatRequest):
    '''用户发来一句话，返回助手的回答'''
    response=agent.run(request.message)
    memory.add_interaction(request.message,response)
    return ChatResponse(reply=response)
if __name__=="__main__":
    uvicorn.run(app,host="0.0.0.0",port=8000)