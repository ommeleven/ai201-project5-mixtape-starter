"""
tests/test_notifications.py - Mixtape

Tests for notification creation.
"""

import pytest

from app import create_app, db
from models import Notification, Song, User
from services.notification_service import rate_song


@pytest.fixture
def app():
    app = create_app({"TESTING": True, "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:"})
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()


def test_rating_friend_song_creates_notification(app):
    """Rating a song shared by another user notifies the original sharer."""
    with app.app_context():
        sharer = User(username="aaliya", email="aaliya@example.com")
        rater = User(username="kenji", email="kenji@example.com")
        db.session.add_all([sharer, rater])
        db.session.flush()

        song = Song(title="Golden Hour", artist="Solange K", shared_by=sharer.id)
        db.session.add(song)
        db.session.commit()

        rate_song(rater.id, song.id, 5)

        notification = db.session.query(Notification).filter_by(user_id=sharer.id).one()
        assert notification.notification_type == "song_rated"
        assert "kenji rated your song 'Golden Hour' 5 stars." == notification.body
