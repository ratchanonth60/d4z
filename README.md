#  FastAPI Project: d4z 🚀

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.13+-blue.svg?style=for-the-badge&logo=python&logoColor=white" alt="Python 3.13+">
  <img src="https://img.shields.io/badge/FastAPI-latest-green.svg?style=for-the-badge&logo=fastapi&logoColor=white" alt="FastAPI">
  <img src="https://img.shields.io/badge/SQLModel-latest-purple.svg?style=for-the-badge" alt="SQLModel">
  <img src="https://img.shields.io/badge/PostgreSQL-latest-blue.svg?style=for-the-badge&logo=postgresql&logoColor=white" alt="PostgreSQL">
  <img src="https://img.shields.io/badge/Docker-Powered-blue.svg?style=for-the-badge&logo=docker&logoColor=white" alt="Docker Powered">
  <img src="https://img.shields.io/badge/License-Apache_2.0-orange.svg?style=for-the-badge" alt="License">
</p>

A modern web application built with **FastAPI**, featuring secure authentication, asynchronous PostgreSQL database integration using **SQLModel**, and a well-structured API design.

## ✨ Features

* **🚀 High-Performance API:** Built with [FastAPI](https://fastapi.tiangolo.com/) for rapid development and high performance.
* **🐘 Asynchronous PostgreSQL Integration:** Utilizes `asyncpg` for non-blocking database operations.
* **🔮 ORM with SQLModel:** Leverages [SQLModel](https://sqlmodel.tiangolo.com/) for intuitive database interaction, combining Pydantic and SQLAlchemy.
* **🛡️ Secure Authentication:**
    * OAuth2 Password Flow for token-based authentication.
    * JWT (JSON Web Tokens) for access and refresh tokens using `PyJWT`.
    * Refresh Token rotation and server-side session management for enhanced security.
    * Password hashing using `passlib` (bcrypt).
    * Logout and Logout All functionality.
* **📄 Standardized API Responses:** Uses a `BaseResponse` model for consistent success and error responses.
* **📖 Pagination, Filtering & Sorting:** Robust support for paginating, filtering, and sorting list results (e.g., user lists).
* **🐳 Dockerized Environment:** Easy setup and deployment using Docker and Docker Compose.
* **🔧 Development & Debugging:**
    * Live reload for development.
    * `debugpy` support for debugging within Docker containers.
* **⚙️ Configuration Management:** Uses `pydantic-settings` for managing configurations via environment variables and `.env` files.
* **📜 Custom Exception Handling:** Centralized handlers for various exception types.
* **↔️ CORS & GZip Middleware:** Configured for Cross-Origin Resource Sharing and GZip compression.
* **💅 Code Quality:** Configured with `flake8` for linting.

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
        * `SECRET_KEY` (a strong, random key for JWTs)
        * `ACCESS_TOKEN_EXPIRE_MINUTES`, `REFRESH_TOKEN_EXPIRE_MINUTES`
    * The `DATABASE_URL` should be correctly set for `asyncpg` (e.g., `postgresql+asyncpg://user:password@db:5432/dbname`). If `DATABASE_URL` is not in `.env`, `app/core/config.py` will construct it.

3.  **Build and run the application using Docker Compose:**
    ```bash
    docker-compose up --build -d
    ```
   
    The application will typically be available at `http://localhost:8000`.

### 💻 Manual Installation (Alternative)

1.  **Create a virtual environment:**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```
   

2.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    # pip install -r requirements-dev.txt # If you have development specific dependencies
    ```
   

3.  **Set up environment variables:**
    * Create a `.env` file as described in the Docker section.

4.  **Ensure PostgreSQL is running** and accessible.

5.  **Run the application using Uvicorn:**
    ```bash
    uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
    ```
    (adapted from docker command)

## 🐛 Development & Debugging

* The project uses `debugpy` for debugging support when running with Docker.
* The debugger attaches to port `5678`.
* Use `flake8 .` for linting.

## 📚 API Documentation

Once the application is running, you can access the interactive API documentation:
* **Swagger UI:** `http://localhost:8000/docs`
* **ReDoc:** `http://localhost:8000/redoc`

## 📁 Project Structure
.
├── app/                    # Application source code
│   ├── api/                # API routers and endpoints
│   ├── core/               # Core components (config, security, dependencies, exceptions)
│   ├── db/                 # Database related (session, SQLModel setup)
│   ├── models/             # SQLModel table models & Pydantic input/output models
│   ├── schemas/            # Pydantic schemas (if separate from models)
│   ├── services/           # Business logic layer
│   ├── middlewares/        # Custom middlewares
│   ├── contextmanager.py   # Lifespan context manager
│   ├── main.py             # Main FastAPI application instance
│   └── settings.py         # FastAPI app configuration assembly
├── .env.example            # Example environment variables (ควรสร้างไฟล์นี้)
├── .flake8                 # Flake8 configuration
├── Dockerfile              # Docker configuration
├── docker-compose.yml      # Docker Compose configuration
├── requirements.txt        # Python dependencies
└── README.md               # This file


 (adapted and expanded)

## ⚖️ License

This project is licensed under the terms of the Apache 2.0 license. See `LICENSE` file for details.
(Your original README mentions "included LICENSE file", ensure you have one or specify the license if different.)

## 🤝 Contributing

Contributions are welcome! Please follow these steps:
1.  Fork the repository.
2.  Create your feature branch (`git checkout -b feature/amazing-feature`).
3.  Commit your changes (`git commit -m 'Add some amazing feature'`).
4.  Push to the branch (`git push origin feature/amazing-feature`).
5.  Open a Pull Request.

---

_This README was generated with assistance from an AI. Always review and tailor to your project's specific needs._

