# Windows compatibility fix for CrewAI
import sys
import signal
if sys.platform == 'win32':
    # Windows doesn't have POSIX signals - set dummy values for all common POSIX signals
    posix_signals = {
        'SIGHUP': 1, 'SIGQUIT': 3, 'SIGTSTP': 20, 'SIGCONT': 18,
        'SIGTTOU': 22, 'SIGTTIN': 21, 'SIGUSR1': 10, 'SIGUSR2': 12,
        'SIGCHLD': 17, 'SIGPIPE': 13, 'SIGALRM': 14, 'SIGWINCH': 28,
        'SIGIO': 29, 'SIGPROF': 27, 'SIGVTALRM': 26, 'SIGPWR': 30,
        'SIGSYS': 31, 'SIGURG': 23, 'SIGXCPU': 24, 'SIGXFSZ': 25
    }
    for sig_name, sig_val in posix_signals.items():
        if not hasattr(signal, sig_name):
            setattr(signal, sig_name, sig_val)

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import analysis, health, sessions, voice, report, news, sharing
from app.core.config import API_METADATA, CORS_ORIGINS
from app.core.db import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.db = init_db()
    print("[API] Database initialized successfully")
    yield


app = FastAPI(**API_METADATA, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(sessions.router)
app.include_router(analysis.router)
app.include_router(voice.router)
app.include_router(report.router)
app.include_router(news.router)
app.include_router(sharing.router)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.api.main:app", host="0.0.0.0", port=8000, reload=True)


# {
#   "status": "success",
#   "message": "Semaglutide shows promising repurposing signals...",
#   "session": {
#     "sessionId": "...",
#     "title": "...",
#     "chatHistory": [
#       { "role": "user", "content": "..." },
#       { "role": "assistant", "content": "..." }
#     ],
#     "agentsData": {
#       "iqvia": { ... },
#       "exim": { ... },
#       "patent": { ... },
#       "clinical": { ... },
#       "internal": { ... },
#       "report": { ... }
#     },
#     "workflowState": { ... }
#   },
#   "meta": {}
# }
