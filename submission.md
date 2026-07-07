# Mixtape Bug Hunt Submission

## AI Usage

I used AI tools during this project to help navigate an unfamiliar codebase and understand existing patterns.

I used AI for:
- Summarizing the responsibility of unfamiliar files and services.
- Helping trace execution flow between routes, services, and models.
- Explaining Python behavior and SQLAlchemy patterns while investigating possible bugs.

I verified AI suggestions by reading the source code, reproducing issues locally, and testing each fix before committing. AI was used as a navigation and explanation tool rather than as a replacement for debugging.

---

# Codebase Map

## Main Files and Responsibilities

### app.py

The Flask application factory.

Responsibilities:
- Creates the Flask application.
- Configures the database.
- Registers route blueprints.

---

### models.py

Defines SQLAlchemy database models.

Main models include:
- User
- Song
- Playlist
- PlaylistSong
- Notification

Models define relationships between users, songs, playlists, and notifications.

---

### seed_data.py

Creates initial database data used for local development and testing.

---

### routes/

Contains API endpoints.

Files:

- `routes/users.py`
  - User-related endpoints including profile and notifications.

- `routes/songs.py`
  - Song searching, rating, and song actions.

- `routes/playlists.py`
  - Playlist creation and playlist song operations.

- `routes/feed.py`
  - Feed-related endpoints.

Routes handle HTTP requests and delegate business logic to services.

---

### services/

Contains application business logic.

Files:

- `search_service.py`
  - Handles song search functionality.

- `notification_service.py`
  - Creates and retrieves notifications.

- `playlist_service.py`
  - Handles playlist operations.

- `feed_service.py`
  - Generates user feeds.

- `streak_service.py`
  - Calculates listening streaks.

---

# Data Flow Example

## User rates a song

1. User sends:

2. Request is handled by:

3. Route calls the song-related service logic.

4. Song rating information is updated in the database.

5. Notification service creates a notification for the song owner.

6. API returns the response.

---

# Patterns Observed

- Routes are thin layers responsible for HTTP handling.
- Services contain application logic.
- SQLAlchemy models represent database entities.
- Features communicate through service functions.
- Notifications are created through a centralized notification service.

---

# Root Cause Analysis