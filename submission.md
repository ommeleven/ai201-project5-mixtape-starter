# Mixtape Bug Hunt Submission

## AI Usage

I used AI tools to help navigate the unfamiliar codebase, summarize service responsibilities, trace route-to-service call chains, and sanity-check edge cases. I verified suggestions by reading the source, reproducing the bugs with tests or controlled service calls, and running the full test suite after each fix.

## Codebase Map

### Main Files and Responsibilities

- `app.py`: Flask application factory. It configures SQLAlchemy, registers the `songs`, `playlists`, `users`, and `feed` blueprints, and creates database tables.
- `models.py`: SQLAlchemy data model. It defines `User`, `Song`, `Tag`, `ListeningEvent`, `Rating`, `Playlist`, and `Notification`, plus association tables for friendships, song tags, and ordered playlist entries.
- `routes/`: HTTP layer. Routes parse request data, call service functions, and format JSON responses.
- `services/`: Business logic layer. Streak calculation, search, feed filtering, playlist retrieval, and notification creation all live here.
- `seed_data.py`: Local development data with users, friendships, tagged songs, listening events, playlists, and sample notifications.
- `tests/`: Regression tests for service behavior.

### Data Flow Example: Rating a Song

1. A client sends `POST /songs/<song_id>/rate` with `user_id` and `score`.
2. `routes/songs.py` validates the request body and calls `notification_service.rate_song(user_id, song_id, score)`.
3. `rate_song()` loads the `Song` and rating `User`, validates the score, and creates or updates a `Rating` row.
4. If the rater is not the original sharer, `rate_song()` creates a `Notification` for the song's `shared_by` user.
5. The route returns the saved rating as JSON.

### Patterns Observed

- Routes stay thin and delegate business rules to services.
- Service functions raise `ValueError` for invalid IDs or inputs; routes translate those into JSON errors.
- Models expose `to_dict()` helpers so services and routes can return consistent API shapes.
- Notifications are centralized through `create_notification()`.
- Playlist ordering is stored on the `playlist_entries` association table, not on `Song`.

## Root Cause Analysis

### Issue #1: Listening Streak Resets on Sunday

**How I reproduced it:** I used the existing streak test that listens on Saturday, June 15, 2024, then Sunday, June 16, 2024. Before the fix, the streak stayed at `1` instead of increasing to `2`.

**Navigation strategy:** I traced `POST /songs/<song_id>/listen` in `routes/songs.py` to `record_listening_event()` and then `update_listening_streak()` in `services/streak_service.py`.

**Root cause:** `update_listening_streak()` only incremented consecutive-day streaks when `today.weekday() != 6`. In Python, `weekday() == 6` means Sunday, so Saturday-to-Sunday listening was treated like a missed day.

**Fix:** Removed the Sunday exclusion. Any `days_since_last == 1` now increments the streak.

**Verification:** `test_streak_increments_on_sunday` passes, along with the full suite: `15 passed`.

### Issue #2: Friends Listening Now Shows Yesterday's Events

**How I reproduced it:** I added a regression test where the current time is Tuesday, July 7, 2026 at 9:00 AM UTC and a friend listened Monday night at 11:00 PM UTC. Before the fix, that event was within 24 hours and appeared in "listening now."

**Navigation strategy:** I traced `GET /feed/<user_id>/listening-now` in `routes/feed.py` to `get_friends_listening_now()` in `services/feed_service.py`.

**Root cause:** The service used a rolling 24-hour threshold. The product expectation is "today," so previous-night events remained visible until they became more than 24 hours old.

**Fix:** Changed the cutoff to the start of the current UTC calendar day.

**Verification:** Added `tests/test_feed.py`; `test_listening_now_excludes_yesterday_events` passes, along with the full suite.

### Issue #3: Duplicate Songs in Search Results

**How I reproduced it:** I searched for a song with multiple tags, such as "Crown Heights Anthem." Without deduplication, the tag join can return one row per matching tag association.

**Navigation strategy:** I traced `GET /songs/search?q=...` in `routes/songs.py` to `search_songs()` in `services/search_service.py`.

**Root cause:** Searching joins through `song_tags`; songs with multiple tag rows can appear multiple times unless the query deduplicates `Song` rows.

**Fix:** Added `.distinct()` to the search query so each matching song appears once.

**Verification:** Existing search regression tests pass, including `test_search_no_duplicates_multi_tag_song`.

### Issue #4: Rating a Song Does Not Notify the Sharer

**How I reproduced it:** I created a song shared by `aaliya`, rated it as `kenji`, then queried `Notification` for `aaliya`. Before the fix, the rating existed but no notification was created.

**Navigation strategy:** I compared the working playlist-add notification path in `notification_service.add_to_playlist()` with the rating path in `notification_service.rate_song()`.

**Root cause:** `rate_song()` saved the rating and committed it, but did not call `create_notification()`. The notification behavior existed for playlist adds but was missing from the rating workflow.

**Fix:** After saving the rating, `rate_song()` now creates a `song_rated` notification for the original sharer unless the user rated their own song.

**Verification:** Added `tests/test_notifications.py`; `test_rating_friend_song_creates_notification` passes, along with the full suite.

### Issue #5: Last Song in Playlist Never Shows Up

**How I reproduced it:** I used the playlist test fixture with five ordered songs. Before the fix, `get_playlist_songs()` returned four songs and omitted `Track 5`.

**Navigation strategy:** I traced `GET /playlists/<playlist_id>/songs` in `routes/playlists.py` to `get_playlist_songs()` in `services/playlist_service.py`.

**Root cause:** The service queried all playlist songs in order, then returned `songs[:-1]`, slicing off the final item every time.

**Fix:** Returned the full ordered list of songs.

**Verification:** `test_playlist_returns_all_songs` and `test_playlist_returns_songs_in_order` pass, along with the full suite.

## Regression Tests

I added regression tests for Issue #2 and Issue #4:

- `tests/test_feed.py`
- `tests/test_notifications.py`

I also ran the existing tests for Issues #1, #3, and #5.

## Final Verification

Command run:

```bash
.venv/bin/python -m pytest tests/
```

Result: `15 passed`.
