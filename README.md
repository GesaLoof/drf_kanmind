# KanMind Backend

A Django REST Framework backend for a Kanban-style task management application. Users can register, log in, create boards, manage tasks and leave comments.

---

## Tech Stack

- Python 3.13
- Django 6.0
- Django REST Framework
- SQLite (development)
- Token Authentication

---

## Installation

**1. Clone the repository**
```bash
git clone https://github.com/GesaLoof/drf_kanmind
cd drf_kanmind
```

**2. Create and activate a virtual environment**
```bash
micromamba create -n django python=3.13
micromamba activate django
```

**3. Install dependencies**
```bash
pip install django djangorestframework django-cors-headers
```

**4. Create a `.env` file** in the project root:
```
SECRET_KEY=your-secret-key-here
DEBUG=True
```

**5. Run migrations**
```bash
python manage.py migrate
```

**6. Create a superuser (optional)**
```bash
python manage.py createsuperuser
```

**7. Start the development server**
```bash
python manage.py runserver
```

The API will be available at `http://127.0.0.1:8000/`

---

## Environment Variables

| Variable | Description |
|----------|-------------|
| `SECRET_KEY` | Django secret key |
| `DEBUG` | Set to `True` for development, `False` for production |

---

## API Endpoints

### Authentication

| Method | URL | Description | Auth required |
|--------|-----|-------------|---------------|
| POST | `/api/register/` | Register a new user | No |
| POST | `/api/login/` | Login and receive token | No |
| POST | `/api/logout/` | Logout and invalidate token | Yes |

**Register body:**
```json
{
    "fullname": "Max Mustermann",
    "email": "max@example.com",
    "password": "yourpassword",
    "repeated_password": "yourpassword"
}
```

**Login body:**
```json
{
    "email": "max@example.com",
    "password": "yourpassword"
}
```

**Login response:**
```json
{
    "token": "abc123...",
    "fullname": "Max Mustermann",
    "email": "max@example.com",
    "user_id": 1
}
```

---

### Boards

| Method | URL | Description | Auth required |
|--------|-----|-------------|---------------|
| GET | `/api/boards/` | List all boards | Yes |
| POST | `/api/boards/` | Create a board | Yes |
| GET | `/api/boards/{id}/` | Get board details | Yes (owner or member) |
| PATCH | `/api/boards/{id}/` | Update a board | Yes (owner or member) |
| DELETE | `/api/boards/{id}/` | Delete a board | Yes (owner or member) |

**Create board body:**
```json
{
    "title": "Projekt X",
    "members": [1, 2, 3]
}
```

**Board list response:**
```json
{
    "id": 1,
    "title": "Projekt X",
    "member_count": 3,
    "ticket_count": 0,
    "tasks_to_do_count": 0,
    "tasks_high_prio_count": 0,
    "owner_id": 1
}
```

**Board detail response:**
```json
{
    "id": 1,
    "title": "Projekt X",
    "owner_id": 1,
    "members": [
        {
            "id": 1,
            "email": "max@example.com",
            "fullname": "Max Mustermann"
        }
    ],
    "tasks": []
}
```

---

### Tasks

| Method | URL | Description | Auth required |
|--------|-----|-------------|---------------|
| GET | `/api/tasks/` | List all tasks | Yes |
| POST | `/api/tasks/` | Create a task | Yes (board member) |
| GET | `/api/tasks/{id}/` | Get task details | Yes (board owner or member) |
| PATCH | `/api/tasks/{id}/` | Update a task | Yes (board owner or member) |
| DELETE | `/api/tasks/{id}/` | Delete a task | Yes (board owner or member) |
| GET | `/api/tasks/assigned-to-me/` | Get tasks assigned to logged in user | Yes |

**Create task body:**
```json
{
    "board": 1,
    "title": "API dokumentieren",
    "description": "Die API Dokumentation vervollständigen",
    "status": "to-do",
    "priority": "high",
    "assignee_id": 1,
    "reviewer_id": 2,
    "due_date": "2025-02-25"
}
```

**Status options:** `to-do`, `in-progress`, `review`, `done`

**Priority options:** `low`, `medium`, `high`

---

### Comments

| Method | URL | Description | Auth required |
|--------|-----|-------------|---------------|
| GET | `/api/tasks/{task_id}/comments/` | List comments for a task | Yes |
| POST | `/api/tasks/{task_id}/comments/` | Add a comment to a task | Yes |

**Create comment body:**
```json
{
    "content": "this is a comment"
}
```

---

### Utility

| Method | URL | Description | Auth required |
|--------|-----|-------------|---------------|
| GET | `/api/email-check/?email=x@x.com` | Check if email exists | No |
| GET | `/api/test/` | API health check | No |

---

## Authentication

This API uses **Token Authentication**. After logging in, include the token in every request header:

```
Authorization: Token your-token-here
```

---

## Permissions

| Resource | List | Detail | Create | Update | Delete |
|----------|------|--------|--------|--------|--------|
| Boards | Any authenticated user | Owner or member | Any authenticated user | Owner or member | Owner or member |
| Tasks | Any authenticated user | Board owner or member | Board owner or member | Board owner or member | Board owner or member |
| Comments | Any authenticated user | - | Any authenticated user | - | - |

---

## CORS

Allowed origins are configured in `settings.py`. For local frontend development add your frontend URL to `CORS_ALLOWED_ORIGINS`:

```python
CORS_ALLOWED_ORIGINS = [
    "http://localhost:5500",
    "http://127.0.0.1:5500",
]
```

---

## Project Structure

```
drf_kanmind/
├── core/                 # Main project settings and URLs
│   ├── settings.py
│   └── urls.py
├── auth_app/             # User registration, login, logout
│   ├── models.py         # Profile model
│   └── api/
│       ├── views.py
│       ├── serializers.py
│       └── urls.py
├── board_app/            # Boards, tasks and comments
│   ├── models.py         # Board, Task, Comment models
│   └── api/
│       ├── views.py
│       ├── serializers.py
│       └── urls.py
├── manage.py
├── .env                  # Not committed to git
├── .gitignore
└── README.md
```


# the text in this README.md was claude generated and human proofread
