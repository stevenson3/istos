from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import books, graph, search, verses

app = FastAPI(
    title="Istos",
    description="Bible-as-Graph API — verses, edges, and linguistic data",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(books.router)
app.include_router(verses.router)
app.include_router(graph.router)
app.include_router(search.router)


@app.get("/healthz")
def health():
    return {"status": "ok"}
