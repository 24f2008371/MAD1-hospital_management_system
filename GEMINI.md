# GEMINI.md

## Project Overview

This project is a Flask-based Hospital Management System. It provides a web interface for managing doctors, patients, and appointments. The application uses a SQLite database and includes features for user authentication and role-based access control (admin, doctor, patient). The frontend is built with Bootstrap and includes a modern, responsive design.

### Key Technologies

*   **Backend:** Flask, Flask-SQLAlchemy, Flask-Login
*   **Database:** SQLite
*   **Frontend:** Bootstrap, HTML, CSS

## Building and Running

### Prerequisites

*   Python 3
*   pip

### Installation

1.  Clone the repository.
2.  Create a virtual environment:
    ```bash
    python -m venv venv
    ```
3.  Activate the virtual environment:
    *   **Windows:**
        ```bash
        venv\Scripts\activate
        ```
    *   **macOS/Linux:**
        ```bash
        source venv/bin/activate
        ```
4.  Install the dependencies:
    ```bash
    pip install -r requirements.txt
    ```

### Running the Application

1.  Run the `app.py` file:
    ```bash
    python app.py
    ```
2.  The application will be available at `http://127.0.0.1:5000`.

### Default Admin Credentials

*   **Username:** admin
*   **Password:** 1234

## Development Conventions

*   The application follows a standard Flask project structure.
*   Database models are defined in `application/models.py`.
*   Routes are defined in `application/controllers.py`.
*   Templates are located in the `templates` directory.
*   Static files (CSS, images) are located in the `static` directory.
