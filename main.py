from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from database import SessionLocal, Thread, Message
import google.generativeai as genai

genai.configure(
    api_key="AIzaSyBA-dgzqU6Is7tCqTe0Imgk41iVj0lslHY"
)

model = genai.GenerativeModel("gemini-1.5-flash")

app = FastAPI(title="Mini AI Chat")


class ThreadRequest(BaseModel):
    title: str


class ChatRequest(BaseModel):
    thread_id: int
    message: str


@app.get("/")
def home():
    return {"message": "AI Chat Running"}


@app.post("/threads")
def create_thread(req: ThreadRequest):

    db = SessionLocal()

    thread = Thread(title=req.title)

    db.add(thread)
    db.commit()
    db.refresh(thread)

    db.close()

    return {
        "thread_id": thread.id,
        "title": thread.title
    }


@app.get("/threads")
def get_threads():

    db = SessionLocal()

    threads = db.query(Thread).all()

    result = []

    for t in threads:
        result.append({
            "id": t.id,
            "title": t.title
        })

    db.close()

    return result


@app.get("/threads/{thread_id}/messages")
def get_messages(thread_id: int):

    db = SessionLocal()

    messages = (
        db.query(Message)
        .filter(Message.thread_id == thread_id)
        .order_by(Message.id)
        .all()
    )

    result = []

    for msg in messages:
        result.append({
            "role": msg.role,
            "content": msg.content
        })

    db.close()

    return result


@app.post("/chat")
def chat(req: ChatRequest):

    db = SessionLocal()

    thread = (
        db.query(Thread)
        .filter(Thread.id == req.thread_id)
        .first()
    )

    if not thread:
        raise HTTPException(
            status_code=404,
            detail="Thread not found"
        )

    user_message = Message(
        thread_id=req.thread_id,
        role="user",
        content=req.message
    )

    db.add(user_message)
    db.commit()

    thread_messages = (
        db.query(Message)
        .filter(Message.thread_id == req.thread_id)
        .order_by(Message.id)
        .all()
    )

    thread_context = "\n".join([
        f"{m.role}: {m.content}"
        for m in thread_messages
    ])

    all_messages = (
        db.query(Message)
        .order_by(Message.id)
        .all()
    )

    memory_context = "\n".join([
        f"{m.role}: {m.content}"
        for m in all_messages[-30:]
    ])

    prompt = f"""
You are a helpful AI assistant.

Universal Memory:
{memory_context}

Current Thread:
{thread_context}

User:
{req.message}
"""

    response = model.generate_content(prompt)

    ai_text = response.text

    ai_message = Message(
        thread_id=req.thread_id,
        role="assistant",
        content=ai_text
    )

    db.add(ai_message)
    db.commit()

    db.close()

    return {
        "response": ai_text
    }   