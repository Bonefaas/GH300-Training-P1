# Mergington High School Activities API

A super simple FastAPI application that allows students to view and sign up for extracurricular activities.

## Features

- View all available extracurricular activities
- See registered participants on each activity card and unregister them using the delete icon
- Sign up for activities

## Getting Started

1. Install the dependencies:

   ```
   pip install fastapi uvicorn
   ```

2. Run the application:

   ```
   python app.py
   ```

3. Open your browser and go to:
   - API documentation: http://localhost:8000/docs
   - Alternative documentation: http://localhost:8000/redoc

## Debugging in VS Code

From the repository root, select **Launch Mergington WebApp** in Run and Debug
and press **F5**. The configuration reloads the server when Python or static
files change. Keep `--reload-include=src/static/*` as a single argument so
Windows command-line wildcard expansion does not turn the pattern into
multiple filenames.

Static assets revalidate with the server so new page loads pick up updated
scripts and styles. If an already-open tab is running an older script, press
**Ctrl+Shift+R** once. Signups and unregister actions then refresh the activity
cards automatically without reloading the page.

## API Endpoints

| Method | Endpoint                                                          | Description                                                         |
| ------ | ----------------------------------------------------------------- | ------------------------------------------------------------------- |
| GET    | `/activities`                                                     | Get all activities with their details and current participant count |
| POST   | `/activities/{activity_name}/signup?email=student@mergington.edu` | Sign up for an activity                                             |
| DELETE | `/activities/{activity_name}/unregister?email=student@mergington.edu` | Unregister a participant from an activity |

Signing up with an email already registered for that activity returns HTTP 400
with the detail `Student is already signed up for this activity`.

Unregistering refreshes the participant list and available spots. An unknown
activity or a student not registered for that activity returns HTTP 404.

## Data Model

The application uses a simple data model with meaningful identifiers:

1. **Activities** - Uses activity name as identifier:

   - Description
   - Schedule
   - Maximum number of participants allowed
   - List of student emails who are signed up

2. **Students** - Uses email as identifier:
   - Name
   - Grade level

All data is stored in memory, which means data will be reset when the server restarts.
