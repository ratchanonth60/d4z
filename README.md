# FastAPI Project: d4z 🚀

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.13+-blue.svg?style=for-the-badge&logo=python&logoColor=white" alt="Python 3.13+">
  <img src="https://img.shields.io/badge/FastAPI-latest-green.svg?style=for-the-badge&logo=fastapi&logoColor=white" alt="FastAPI">
  <img src="https://img.shields.io/badge/Celery-latest-green.svg?style=for-the-badge&logo=celery&logoColor=white" alt="Celery">
  <img src="https://img.shields.io/badge/Tortoise_ORM-latest-blue.svg?style=for-the-badge" alt="Tortoise ORM">
  <img src="https://img.shields.io/badge/Aerich-Migrations-lightgrey.svg?style=for-the-badge" alt="Aerich Migrations">
  <img src="https://img.shields.io/badge/PostgreSQL-latest-blue.svg?style=for-the-badge&logo=postgresql&logoColor=white" alt="PostgreSQL">
  <img src="https://img.shields.io/badge/Redis-latest-red.svg?style=for-the-badge&logo=redis&logoColor=white" alt="Redis">
  <img src="https://img.shields.io/badge/Pytest-Testing-purple.svg?style=for-the-badge&logo=pytest&logoColor=white" alt="Pytest">
  <img src="https://img.shields.io/badge/Docker-Powered-blue.svg?style=for-the-badge&logo=docker&logoColor=white" alt="Docker Powered">
  <img src="https://img.shields.io/badge/License-Apache_2.0-orange.svg?style=for-the-badge" alt="License">
</p>

A modern web application built with **FastAPI**, featuring secure authentication with email verification, asynchronous PostgreSQL database integration using **Tortoise ORM**, database migrations managed by **Aerich**, asynchronous email sending via **Celery** with **Redis** as a message broker, and a comprehensive testing suite with **Pytest**.

## ✨ Features

* **🚀 High-Performance API:** Built with [FastAPI](https://fastapi.tiangolo.com/) for rapid development and high performance.
* **🐘 Asynchronous PostgreSQL Integration:** Utilizes `asyncpg` via Tortoise ORM for non-blocking database operations.
* **🐢 ORM with Tortoise ORM:** Leverages [Tortoise ORM](https://tortoise.github.io/) for intuitive asynchronous database interaction.
* **✈️ Database Migrations with Aerich:** Manages database schema changes using Aerich, a migration tool for Tortoise ORM.
* **🛡️ Secure Authentication:**
    * User registration with email verification (users are inactive until email is confirmed).
    * OAuth2 Password Flow for token-based authentication.
    * JWT (JSON Web Tokens) for access and refresh tokens using `PyJWT`, including `jti` claim for enhanced uniqueness.
    * Refresh Token rotation and server-side session management for enhanced security.
    * Password hashing using `passlib` (bcrypt).
    * Logout functionality.
* **Task Processing with Celery:**
    * **📧 Asynchronous Email Sending:** Email notifications (e.g., verification emails) are sent via Celery tasks, preventing blocking of API responses.
    * **📈 Scalable Background Workers:** Celery workers can be scaled independently to handle varying loads of background tasks.
    * **Reliable Message Queuing with Redis:** Uses Redis as a robust message broker for Celery.
* **📧 Email Integration with `fastapi-mail`:** Sends HTML templated emails for verification (now processed by Celery).
* **🧪 Testing with Pytest:**
    * Comprehensive unit and integration tests using `pytest` and `pytest-asyncio`.
    * Test environment configured to use a dedicated PostgreSQL test database.
    * Automated creation and teardown of the test database instance and schemas.
* **📄 Standardized API Responses:** Uses a `BaseResponse` model for consistent success and error responses.
* **📖 Pagination, Filtering & Sorting:** Robust support for paginating, filtering, and sorting list results.
* **🐳 Dockerized Environment:** Easy setup and deployment using Docker and Docker Compose for the main application, database, Redis, and Celery workers.
* **🔧 Development & Debugging:**
    * Live reload for development.
    * `debugpy` support for debugging within Docker containers.
* **⚙️ Configuration Management:** Uses `pydantic-settings` for managing configurations via environment variables and `.env` files.
* **📜 Custom Exception Handling:** Centralized handlers for various exception types.
* **↔️ CORS & GZip Middleware:** Configured for Cross-Origin Resource Sharing and GZip compression.

## 🛠️ Prerequisites

* Python 3.13 or higher
* Docker and Docker Compose
* PostgreSQL server (if running locally without Docker, or for the test database)
* Redis server (if running locally without Docker for Celery broker)

## 🚀 Getting Started

### 🐳 Using Docker (Recommended)

1.  **Clone the repository:**
    ```bash
    git clone <repository-url>
    cd <project-directory>
    ```

2.  **Environment Variables (`.env`):**
    * Copy `.env.example` (if one exists) to `.env`.
    * Update the `.env` file with your settings. Key variables include:
        * `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`, `POSTGRES_SERVER`, `POSTGRES_PORT`.
        * `DATABASE_DSN` (e.g., `asyncpg://user:password@db:5432/dbname`).
        * `SECRET_KEY` (a strong, random key for JWTs).
        * `ACCESS_TOKEN_EXPIRE_MINUTES`, `REFRESH_TOKEN_EXPIRE_MINUTES`.
        * Mail server settings (`MAIL_USERNAME`, `MAIL_PASSWORD`, etc.).
        * `BASE_URL` (e.g., `http://localhost:8000`) for email verification links.
        * **Celery Settings:**
            * `CELERY_BROKER_URL` (e.g., `redis://redis:6379/0`)
            * `CELERY_RESULT_BACKEND` (e.g., `redis://redis:6379/0`)
        * **For Testing (if running tests locally against a non-Dockerized PostgreSQL test DB):**
            * `TEST_POSTGRES_USER`, `TEST_POSTGRES_PASSWORD`, `TEST_POSTGRES_SERVER`, `TEST_POSTGRES_PORT`, `TEST_POSTGRES_DB`.
            * `TEST_DATABASE_DSN` (e.g., `asyncpg://test_user:test_password@localhost:5432/mydatabase_test`).
    * The `app/core/config.py` file loads these settings.

3.  **Build and run the application using Docker Compose:**
    ```bash
    docker-compose up --build -d
    ```
    This will start the FastAPI application, PostgreSQL database, Redis, and Celery worker(s).
    The application will typically be available at `http://localhost:8000`.

4.  **Database Migrations (Aerich):**
    To generate a new migration:
    ```bash
    docker-compose exec app aerich migrate --name <your_migration_name>
    ```
    To apply migrations:
    ```bash
    docker-compose exec app aerich upgrade
    ```
    (The `app` service in `docker-compose.yml` is also configured to attempt `aerich upgrade` on startup).

### 💻 Manual Installation (Alternative / For Local Testing Setup)

1.  **Create a virtual environment and install dependencies:**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    pip install -r requirements.txt
    ```
    Ensure `requirements.txt` includes `celery[redis]`.

2.  **Set up environment variables** (as described in the Docker section).

3.  **PostgreSQL & Redis Setup:**
    * Ensure your PostgreSQL and Redis servers are running and accessible.
    * Create databases and users as needed.

4.  **Initialize Aerich and run migrations** (as described in the Docker section, but run commands locally).

5.  **Run the FastAPI Application (Uvicorn):**
    ```bash
    uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
    ```

6.  **Run the Celery Worker (Locally):**
    In a separate terminal, navigate to the project root (where `PYTHONPATH` can see the `app` module) and run:
    ```bash
    celery -A app.worker.celery_app worker -l info --concurrency=1
    ```
    (Adjust concurrency as needed).

## 🧪 Testing

This project uses `pytest`. Tests are configured to run against a dedicated PostgreSQL test database.

1.  **Configure Test Database:**
    * Ensure environment variables for the test database are set in `.env`.
    * The PostgreSQL user (`TEST_POSTGRES_USER`) should ideally have `CREATEDB` privileges.
    * Test setup is in `tests/conftest.py`.

2.  **Run Tests:**
    ```bash
    pytest
    ```

## 🐛 Development & Debugging

* `debugpy` is configured for debugging the FastAPI application within Docker.
* For debugging Celery tasks, you can run the worker with a single concurrency (`--concurrency=1`) and use `pdb` or other Python debugging tools within the task code. You can also execute tasks eagerly for debugging by configuring Celery for testing (`task_always_eager = True`), but this bypasses the broker.

## 📚 API Documentation

* **Swagger UI:** `http://localhost:8000/docs`
* **ReDoc:** `http://localhost:8000/redoc`

## 📁 Project Structure

```
.
├── app/
│   ├── api/
│   │   └── v1/
│   │       ├── endpoints/
│   │       │   ├── auth.py
│   │       │   └── users.py
│   │       └── routers.py
│   ├── core/                 # Config, security, dependencies, exceptions
│   ├── db/                   # Database setup (tortoise_config.py)
│   ├── models/               # Tortoise ORM models
│   ├── schemas/              # Pydantic schemas
│   ├── services/             # Business logic
│   ├── tasks/                # Celery tasks (e.g., email_tasks.py)
│   ├── templates/            # Email templates
│   │   └── email/
│   │       └── verification_email.html
│   ├── migrations/           # Aerich migration files
│   ├── worker.py             # Celery application instance setup
│   ├── main.py               # FastAPI app instantiation
│   └── settings.py           # FastAPI app configuration settings
├── tests/                    # Pytest tests
│   ├── conftest.py
│   └── api/
│       └── v1/
│           ├── test_auth.py
│           └── test_users.py
├── .env                      # Environment variables
├── .vscode/                  # VSCode specific settings
│   ├── launch.json
│   └── settings.json
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── aerich.ini
├── pytest.ini
└── README.md
```

## ⚖️ License

This project is licensed under the terms of the Apache 2.0 license.

## 🤝 Contributing

Contributions are welcome! Please follow standard fork, branch, commit, push, and Pull Request procedures.

