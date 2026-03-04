# FastAPI + Pydantic + MongoDB (OOP + Design Patterns)

This starter uses:
- FastAPI for HTTP APIs
- Pydantic v2 for schema validation
- MongoDB with Motor (async driver)
- Repository pattern + Service layer
- Dependency Injection via FastAPI `Depends`
- Singleton-style Mongo client manager

## Project Structure

```text
app/
  api/
    v1/
      routers/
        user_router.py
      api.py
  core/
    config.py
    database.py
  models/
    user.py
  repositories/
    base.py
    user_repository.py
  schemas/
    user.py
  services/
    user_service.py
  dependencies.py
  main.py
requirements.txt
.env.example
```

## Run

1. Create and activate a virtual environment.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Copy env file:
   ```bash
   cp .env.example .env
   ```
4. Start server:
   ```bash
   uvicorn app.main:app --reload
   ```

## Sample Endpoints

- `POST /api/v1/users/`
- `GET /api/v1/users/{user_id}`
- `GET /api/v1/users/`
- `PATCH /api/v1/users/{user_id}/deactivate`
- `GET /api/v1/permissions/{user_id}`
- `PATCH /api/v1/permissions/{user_id}`
- `POST /api/v1/permissions/{user_id}/accept-all`
- `PATCH /api/v1/permissions/{user_id}/microphone`
- `PATCH /api/v1/permissions/{user_id}/notifications`
- `PATCH /api/v1/permissions/{user_id}/contacts`
