# FastAPI Project

A modern web application built with FastAPI, featuring secure authentication and PostgreSQL database integration.

## Features

- FastAPI framework for high-performance API development
- PostgreSQL database integration with asyncpg
- Secure authentication with JWT tokens
- Docker containerization for easy deployment
- Development environment with debugpy support

## Prerequisites

- Python 3.13 or higher
- Docker and Docker Compose
- PostgreSQL (if running locally)

## Installation

### Using Docker (Recommended)

1. Clone the repository:
```bash
git clone <repository-url>
cd <project-directory>
```

2. Start the application using Docker Compose:
```bash
docker-compose up -d
```

### Manual Installation

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables (create a .env file based on .env.example)

4. Run the application:
```bash
uvicorn app.main:app --reload
```

## Development

The project uses debugpy for debugging support. To enable debugging:

1. Set the `DEBUG` environment variable to `true`
2. The debugger will be available on port 5678

## API Documentation

Once the application is running, you can access:
- Swagger UI documentation at `/docs`
- ReDoc documentation at `/redoc`

## Project Structure

```
.
├── app/                    # Application source code
├── .dev/                   # Development configuration
├── Dockerfile             # Docker configuration
├── docker-compose.yml     # Docker Compose configuration
├── requirements.txt       # Python dependencies
└── README.md             # Project documentation
```

## License

This project is licensed under the terms of the included LICENSE file.

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request
