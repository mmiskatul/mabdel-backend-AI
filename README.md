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
        auth_router.py
        permission_router.py
        user_router.py
      api.py
  core/
    config.py
    database.py
    security.py
  models/
    auth.py
    permission.py
    signup_validation.py
    user.py
  repositories/
    auth_repository.py
    base.py
    permission_repository.py
    user_repository.py
  schemas/
    auth.py
    permission.py
    user.py
  services/
    auth_service.py
    permission_service.py
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
   Configure SMTP values in `.env` if you want email OTP delivery.
4. Start server:
   ```bash
   uvicorn app.main:app --reload
   ```

## Sample Endpoints

- `POST /api/v1/auth/signup`
- `POST /api/v1/auth/validate-email`
- `POST /api/v1/auth/login`
- `POST /api/v1/auth/forgot-password/options`
- `POST /api/v1/auth/forgot-password/send-code`
- `POST /api/v1/auth/forgot-password/verify-otp`
- `POST /api/v1/auth/forgot-password/reset-password`
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

## Signup Flow

1. Call `POST /api/v1/auth/validate-email` with:
   ```json
   { "email": "user@example.com" }
   ```
2. If `is_available` is `true`, use returned `signup_validation_token` in `POST /api/v1/auth/signup`:
   ```json
   {
     "full_name": "Mabdel User",
     "email": "user@example.com",
     "phone": "+8801XXXXXXXXX",
     "password": "StrongPass123!",
     "signup_validation_token": "token_from_validate_email",
     "accept_terms": true
   }
   ```
