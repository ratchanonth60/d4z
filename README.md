# FastAPI Project: d4z 🚀

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.13+-blue.svg?style=for-the-badge&logo=python&logoColor=white" alt="Python 3.13+">
  <img src="https://img.shields.io/badge/FastAPI-latest-green.svg?style=for-the-badge&logo=fastapi&logoColor=white" alt="FastAPI">
  <img src="https://img.shields.io/badge/Tortoise_ORM-latest-blue.svg?style=for-the-badge" alt="Tortoise ORM">
  <img src="https://img.shields.io/badge/Aerich-Migrations-lightgrey.svg?style=for-the-badge" alt="Aerich Migrations">
  <img src="https://img.shields.io/badge/PostgreSQL-latest-blue.svg?style=for-the-badge&logo=postgresql&logoColor=white" alt="PostgreSQL">
  <img src="https://img.shields.io/badge/Pytest-Testing-purple.svg?style=for-the-badge&logo=pytest&logoColor=white" alt="Pytest">
  <img src="https://img.shields.io/badge/Docker-Powered-blue.svg?style=for-the-badge&logo=docker&logoColor=white" alt="Docker Powered">
  <img src="https://img.shields.io/badge/License-Apache_2.0-orange.svg?style=for-the-badge" alt="License">
</p>

A modern web application built with **FastAPI**, featuring secure authentication with email verification, asynchronous PostgreSQL database integration using **Tortoise ORM**, database migrations managed by **Aerich**, and a comprehensive testing suite with **Pytest**.

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
* **📧 Email Integration with `fastapi-mail`:** Sends HTML templated emails for verification.
* **🧪 Testing with Pytest:**
    * Comprehensive unit and integration tests using `pytest` and `pytest-asyncio`.
    * Test environment configured to use a dedicated PostgreSQL test database for closer alignment with production.
    * Automated creation and teardown of the test database instance and schemas per test session/function.
* **📄 Standardized API Responses:** Uses a `BaseResponse` model for consistent success and error responses.
* **📖 Pagination, Filtering & Sorting:** Robust support for paginating, filtering, and sorting list results (e.g., user lists).
* **🐳 Dockerized Environment:** Easy setup and deployment using Docker and Docker Compose for the main application and development database.
* **🔧 Development & Debugging:**
    * Live reload for development.
    * `debugpy` support for debugging within Docker containers.
* **⚙️ Configuration Management:** Uses `pydantic-settings` for managing configurations via environment variables and `.env` files.
* **📜 Custom Exception Handling:** Centralized handlers for various exception types.
* **↔️ CORS & GZip Middleware:** Configured for Cross-Origin Resource Sharing and GZip compression.

## 🛠️ Prerequisites

* Python 3.13 or higher
* Docker and Docker Compose (for running the application via Docker)
* PostgreSQL server (if running locally without Docker, or for the test database)

## 🚀 Getting Started

### 🐳 Using Docker (Recommended for Development)

1.  **Clone the repository:**
    ```bash
    git clone <repository-url>
    cd <project-directory>
    ```

2.  **Environment Variables (`.env`):**
    * Copy `.env.example` (if one exists) to `.env`.
    * Update the `.env` file with your settings. Key variables include:
        * `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`, `POSTGRES_SERVER`, `POSTGRES_PORT` (for the main application database, typically managed by Docker Compose).
        * `DATABASE_DSN` (e.g., `asyncpg://user:password@db:5432/dbname`).
        * `SECRET_KEY` (a strong, random key for JWTs).
        * `ACCESS_TOKEN_EXPIRE_MINUTES`, `REFRESH_TOKEN_EXPIRE_MINUTES`.
        * Mail server settings (`MAIL_USERNAME`, `MAIL_PASSWORD`, etc.) for email verification.
        * `BASE_URL` (e.g., `http://localhost:8000`) for email verification links.
        * **For Testing (if running tests locally against a non-Dockerized PostgreSQL test DB):**
            * `TEST_POSTGRES_USER`, `TEST_POSTGRES_PASSWORD`, `TEST_POSTGRES_SERVER`, `TEST_POSTGRES_PORT`, `TEST_POSTGRES_DB`.
            * `TEST_DATABASE_DSN` (e.g., `asyncpg://test_user:test_password@localhost:5432/mydatabase_test`).
    * The `app/core/config.py` file loads these settings.

3.  **Build and run the application using Docker Compose:**
    ```bash
    docker-compose up --build -d
    ```
    The application will typically be available at `http://localhost:8000`.

4.  **Database Migrations (Aerich):**
    Migrations should ideally be run when the application starts or as part of your deployment process. The `docker-compose.yml`'s app service command can be adapted to run migrations.
    To generate a new migration (usually done during development):
    ```bash
    docker-compose exec app aerich migrate --name <your_migration_name>
    ```
    To apply migrations:
    ```bash
    docker-compose exec app aerich upgrade
    ```

### 💻 Manual Installation (Alternative / For Local Testing Setup)

1.  **Create a virtual environment:**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

2.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
    Ensure `requirements.txt` includes `tortoise-orm[asyncpg]`, `aerich`, `pytest`, `pytest-asyncio`, `httpx`, and other necessary packages.

3.  **Set up environment variables:**
    * Create a `.env` file as described in the Docker section, ensuring all necessary variables (including those for the test database if not using Docker for it) are set.

4.  **PostgreSQL Setup:**
    * Ensure your PostgreSQL server is running and accessible.
    * For the main application (if not using Docker DB): Create the main database and user.
    * For testing: You will need a separate PostgreSQL database for tests. The test suite (`tests/conftest.py`) is configured to attempt to create and drop this test database automatically if the configured PostgreSQL user has `CREATEDB` privileges. Otherwise, you may need to create it manually.

5.  **Initialize Aerich (if not already done):**
    * Set up `aerich.ini` (usually created by `aerich init -t app.db.tortoise_config.TORTOISE_ORM_CONFIG`).
    * Run initial migrations for your main database:
        ```bash
        aerich migrate --name initial_setup
        aerich upgrade
        ```

6.  **Run the application (Uvicorn):**
    ```bash
    uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
    ```

## 🧪 Testing

This project uses `pytest` for testing. The tests are configured to run against a dedicated PostgreSQL test database.

1.  **Configure Test Database:**
    * Ensure the environment variables for the test database are set in your `.env` file (e.g., `TEST_POSTGRES_USER`, `TEST_POSTGRES_PASSWORD`, `TEST_POSTGRES_SERVER`, `TEST_POSTGRES_PORT`, `TEST_POSTGRES_DB`, `TEST_DATABASE_DSN`).
    * The PostgreSQL user specified (`TEST_POSTGRES_USER`) should have permissions to connect to the PostgreSQL server and, ideally, `CREATEDB` privileges to allow the test suite to create the test database automatically. If not, create the test database (e.g., `mydatabase_test`) manually before running tests.
    * The test setup is defined in `tests/conftest.py`.

2.  **Run Tests:**
    Navigate to the project root directory and run:
    ```bash
    pytest
    ```
    Or, to run tests with more verbosity:
    ```bash
    pytest -vv
    ```
    The `pytest.ini` file includes `asyncio_mode = auto`.

## 🐛 Development & Debugging

* The project uses `debugpy` for debugging support when running with Docker (configured in `docker-compose.yml` and `.vscode/launch.json`).
* The debugger attaches to port `5678`.
* Linting can be performed using a tool like `flake8`.

## 📚 API Documentation

Once the application is running, access the interactive API documentation:
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
│   ├── db/                   # Database setup (e.g., tortoise_config.py)
│   ├── models/               # Tortoise ORM models (users.py, session.py)
│   ├── schemas/              # Pydantic schemas for API I/O
│   ├── services/             # Business logic (users.py, utils.py)
│   ├── templates/            # Email templates
│   │   └── email/
│   │       └── verification_email.html
│   ├── migrations/           # Aerich migration files
│   ├── main.py               # FastAPI app instantiation and root router
│   └── settings.py           # FastAPI app configuration settings
├── tests/                    # Pytest tests
│   ├── conftest.py           # Pytest fixtures and test setup
│   ├── test_main.py          # Example test
│   └── api/
│       └── v1/
│           ├── test_auth.py  # Authentication endpoint tests
│           └── test_users.py # User endpoint tests
├── .env                      # Environment variables (create from .env.example or define manually)
├── .vscode/                  # VSCode specific settings (e.g., debugger, test discovery)
│   ├── launch.json
│   └── settings.json
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── aerich.ini                # Aerich configuration file
├── pytest.ini                # Pytest configuration file
└── README.md
```

## ⚖️ License

This project is licensed under the terms of the Apache 2.0 license. (Ensure you have a `LICENSE` file or update if different).

## 🤝 Contributing

Contributions are welcome! Please follow these steps:
1.  Fork the repository.
2.  Create your feature branch (`git checkout -b feature/amazing-feature`).
3.  Commit your changes (`git commit -m 'Add some amazing feature'`).
4.  Push to the branch (`git push origin feature/amazing-feature`).
5.  Open a Pull Request.

---
