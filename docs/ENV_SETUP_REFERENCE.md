# Environment Setup Reference

This file is safe to commit and intended as a copy template when creating local `.env` files.

## Backend env file
Create `backend/.env`:

```env
# Backend service and API settings
PYTHONUNBUFFERED=1
FRONTEND_URL=http://localhost:5173

# Authentication
CLERK_PUBLISHABLE_KEY=pk_test_your_publishable_key_here
CLERK_SECRET_KEY=sk_test_your_secret_key_here

# Data storage
MONGO_URI=mongodb://localhost:27017
MONGO_DB_NAME=pharmassist_db
MONGO_CHAT_COLLECTION=chat_sessions

# External providers
GROQ_API_KEY=your_groq_api_key_here
OPENAI_API_KEY=your_openai_api_key_here
COMTRADE_API_KEY=your_un_comtrade_api_key_here
```

## Frontend env file
Create `frontend/.env`:

```env
# Clerk key used by the React app
VITE_CLERK_PUBLISHABLE_KEY=pk_test_your_publishable_key_here

# URL where backend API runs
VITE_API_URL=http://localhost:8000
```

## Notes
- Never commit real keys in `.env` files.
- Keep `.env.example` files as placeholders only.
- Rotate any secret that was accidentally exposed before this cleanup.
