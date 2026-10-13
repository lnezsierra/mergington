# Mergington High School Activities

A FastAPI web application where Mergington High School students can browse
extracurricular activities and register with their school email address.

## Registration Flow

1. Browse the available activities, grouped by category.
2. Click an activity card or its **Register** button.
3. Enter the username portion of a `@mergington.edu` email address.
4. Click **Register** to complete the registration.

The activity list displays each activity's description, schedule, remaining
capacity, and currently registered students.

## Getting Started

1. Install the dependencies:

   ```bash
   pip install -r requirements.txt
   ```

2. Start the development server:

   ```bash
   uvicorn src.app:app --reload
   ```

3. Open the application at <http://127.0.0.1:8000>.

API documentation is available at:

- Swagger UI: <http://127.0.0.1:8000/docs>
- ReDoc: <http://127.0.0.1:8000/redoc>

## API Endpoints

| Method | Endpoint | Description |
| --- | --- | --- |
| `GET` | `/activities` | Return all activities and their registration details |
| `POST` | `/activities/{activity_name}/signup?email=student@mergington.edu` | Register a student for an activity |

The signup endpoint accepts only `@mergington.edu` email addresses and rejects
duplicate registrations for the same activity. Registration is unavailable when
an activity reaches its maximum participant capacity.

## Data Storage

Activities and registrations are stored in memory. All registrations reset when
the application server restarts.
