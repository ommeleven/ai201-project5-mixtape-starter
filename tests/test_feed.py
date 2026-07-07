"""
tests/test_feed.py - Mixtape

Tests for friends listening now feed logic.
"""

from datetime import datetime, timedelta, timezone

import pytest

from app import create_app, db
from models import ListeningEvent, Song, User, friendships
from services.feed_service import get_friends_listening_now


@pytest.fixture
def app():
    app = create_app({"TESTING": True, "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:"})
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()


def test_listening_now_excludes_yesterday_events(app, monkeypatch):
    """A previous-night listen should not appear the next morning."""
    with app.app_context():
        now = datetime(2026, 7, 7, 9, 0, 0, tzinfo=timezone.utc)

        class FixedDateTime(datetime):
            @classmethod
            def now(cls, tz=None):
                return now if tz else now.replace(tzinfo=None)

        monkeypatch.setattr("services.feed_service.datetime", FixedDateTime)

        viewer = User(username="nova", email="nova@example.com")
        friend = User(username="darius", email="darius@example.com")
        db.session.add_all([viewer, friend])
        db.session.flush()

        db.session.execute(friendships.insert().values(user_id=viewer.id, friend_id=friend.id))

        song = Song(title="Late Night Session", artist="Nova Blix", shared_by=friend.id)
        db.session.add(song)
        db.session.flush()

        yesterday = now - timedelta(hours=10)
        db.session.add(
            ListeningEvent(user_id=friend.id, song_id=song.id, listened_at=yesterday)
        )
        db.session.commit()

        assert get_friends_listening_now(viewer.id) == []
