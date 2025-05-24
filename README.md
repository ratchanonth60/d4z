# FastAPI Project: d4z 🚀

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.13+-blue.svg?style=for-the-badge&logo=python&logoColor=white" alt="Python 3.13+">
  <img src="https://img.shields.io/badge/FastAPI-latest-green.svg?style=for-the-badge&logo=fastapi&logoColor=white" alt="FastAPI">
  <img src="https://img.shields.io/badge/Tortoise_ORM-latest-blue.svg?style=for-the-badge" alt="Tortoise ORM">
  <img src="https://img.shields.io/badge/Aerich-Migrations-lightgrey.svg?style=for-the-badge" alt="Aerich Migrations">
  <img src="https://img.shields.io/badge/PostgreSQL-latest-blue.svg?style=for-the-badge&logo=postgresql&logoColor=white" alt="PostgreSQL">
  <img src="https://img.shields.io/badge/Docker-Powered-blue.svg?style=for-the-badge&logo=docker&logoColor=white" alt="Docker Powered">
  <img src="https://img.shields.io/badge/License-Apache_2.0-orange.svg?style=for-the-badge" alt="License">
</p>

A modern web application built with **FastAPI**, featuring secure authentication with email verification, asynchronous PostgreSQL database integration using **Tortoise ORM**, and database migrations managed by **Aerich**.

## ✨ Features

* **🚀 High-Performance API:** Built with [FastAPI](https://fastapi.tiangolo.com/) for rapid development and high performance.
* **🐘 Asynchronous PostgreSQL Integration:** Utilizes `asyncpg` via Tortoise ORM for non-blocking database operations.
* **🐢 ORM with Tortoise ORM:** Leverages [Tortoise ORM](https://tortoise.github.io/) for intuitive asynchronous database interaction.
* **✈️ Database Migrations with Aerich:** Manages database schema changes using Aerich, a migration tool for Tortoise ORM.
* **🛡️ Secure Authentication:**
    * User registration with email verification (users are inactive until email is confirmed).
    * OAuth2 Password Flow for token-based authentication.
    * JWT (JSON Web Tokens) for access and refresh tokens using `PyJWT`.
    * Refresh Token rotation and server-side session management for enhanced security.
    * Password hashing using `passlib` (bcrypt).
    * Logout functionality.
* **📧 Email Integration with `fastapi-mail`:** Sends HTML templated emails for verification.
* **📄 Standardized API Responses:** Uses a `BaseResponse` model for consistent success and error responses.
* **📖 Pagination, Filtering & Sorting:** Robust support for paginating, filtering, and sorting list results (e.g., user lists).
* **🐳 Dockerized Environment:** Easy setup and deployment using Docker and Docker Compose.
* **🔧 Development & Debugging:**
    * Live reload for development.
    * `debugpy` support for debugging within Docker containers.
* **⚙️ Configuration Management:** Uses `pydantic-settings` for managing configurations via environment variables and `.env` files.
* **📜 Custom Exception Handling:** Centralized handlers for various exception types.
* **↔️ CORS & GZip Middleware:** Configured for Cross-Origin Resource Sharing and GZip compression.

## 🛠️ Prerequisites

* Python 3.13 or higher
* Docker and Docker Compose
* PostgreSQL (if running locally without Docker for the DB)

## 🚀 Getting Started

### 🐳 Using Docker (Recommended)

1.  **Clone the repository:**
    ```bash
    git clone <repository-url>
    cd <project-directory>
    ```
   

2.  **Environment Variables:**
    * Copy `.env.example` (if you have one) to `.env`.
    * Update the `.env` file with your desired settings, especially for:
        * `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`
        * `DATABASE_DSN` (e.g., `asyncpg://user:password@db:5432/dbname` for Tortoise ORM)
        * `SECRET_KEY` (a strong, random key for JWTs)
        * `ACCESS_TOKEN_EXPIRE_MINUTES`, `REFRESH_TOKEN_EXPIRE_MINUTES`
        * Mail server settings (`MAIL_USERNAME`, `MAIL_PASSWORD`, `MAIL_FROM`, `MAIL_SERVER`, etc.) for email verification.
        * `BASE_URL` (e.g., `http://localhost:8000`) for generating email verification links.
    * The `app/core/config.py` file is responsible for loading these settings.

3.  **Build and run the application using Docker Compose:**
    ```bash
    docker-compose up --build -d
    ```
   
    The application will typically be available at `http://localhost:8000`.

    **Database Migrations (Aerich):**
    Migrations should ideally be run when the application starts or as part of your deployment process. The `docker-compose.yml`'s app service command has been updated to attempt to run migrations.
    ```yaml
    # Example snippet from docker-compose.yml command:
    # sh -c "... aerich upgrade && python -m debugpy ..."
    ```
    For manual migration generation (usually done during development):
    ```bash
    # Inside the app container or a local env with Aerich configured
    docker-compose exec app aerich migrate --name <your_migration_name>
    docker-compose exec app aerich upgrade
    ```

### 💻 Manual Installation (Alternative)

1.  **Create a virtual environment:**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```
   

2.  **Install dependencies:**
    Update `requirements.txt` to include `tortoise-orm[asyncpg]` (or other driver) and `aerich`, and remove SQLModel/SQLAlchemy.
    ```bash
    pip install -r requirements.txt
    ```
   

3.  **Set up environment variables:**
    * Create a `.env` file as described in the Docker section.

4.  **Initialize Tortoise ORM and Aerich:**
    * Ensure PostgreSQL is running and accessible.
    * Set up `aerich.ini` (usually created by `aerich init`):
        ```bash
        aerich init -t app.db.tortoise_config.TORTOISE_ORM_CONFIG # Adjust path to your Tortoise config
        # Edit aerich.ini to ensure tortoise_orm points to your Tortoise config
        # and location points to your migrations folder (e.g., app/migrations)
        ```
    * Run initial migrations or generate schemas:
        ```bash
        # To generate initial tables if no migrations exist yet (after aerich init)
        # This is usually done once, then migrations handle changes.
        # Alternatively, Tortoise.generate_schemas() can be called in app startup once.
        # For ongoing changes:
        aerich migrate --name initial_setup # or a descriptive name
        aerich upgrade
        ```

5.  **Run the application using Uvicorn:**
    The command in `docker-compose.yml` is a good reference.
    ```bash
    uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
    ```
   

## 🐛 Development & Debugging

* The project uses `debugpy` for debugging support when running with Docker.
* The debugger attaches to port `5678`.
* Use `flake8 .` for linting.

## 📚 API Documentation

Once the application is running, you can access the interactive API documentation:
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
│   ├── services/             # Business logic (users.py)
│   ├── templates/            # Email templates
│   │   └── email/
│   │       └── verification_email.html
│   ├── migrations/           # Aerich migration files (e.g., app/migrations if configured there)
│   ├── main.py               # FastAPI app instantiation and root router
│   └── settings.py           # FastAPI app configuration settings
├── tests/
│   ├── conftest.py
│   ├── test_main.py
│   └── api/
│       └── v1/
│           ├── test_auth.py
│           └── test_users.py
├── .env                      # Environment variables (create from .env.example)
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── aerich.ini                # Aerich configuration file (usually at root or where `aerich init` was run)
└── README.md
```
(Structure adapted to include migrations and email templates)

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
