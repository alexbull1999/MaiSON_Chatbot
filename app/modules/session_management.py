from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_

from ..database.models import GeneralConversation, PropertyConversation


class SessionManager:
    def __init__(self):
        # Anonymous sessions expire after 24 hours of inactivity
        self.anonymous_session_expiry = timedelta(hours=24)
        # Authenticated sessions expire after 30 days of inactivity
        self.authenticated_session_expiry = timedelta(days=30)
        # Archived property conversations are kept indefinitely
        # self.completed_conversation_archive = timedelta(days=90)  # Removing this

    async def cleanup_expired_sessions(self, db: Session) -> int:
        """
        Clean up expired sessions based on user type and conversation status.
        Returns the number of sessions cleaned up.
        """
        now = datetime.utcnow()
        cleaned_count = 0

        # Clean up anonymous general conversations
        anonymous_expiry = now - self.anonymous_session_expiry
        expired_anonymous = (
            db.query(GeneralConversation)
            .filter(
                and_(
                    GeneralConversation.is_logged_in == False,  # noqa: E712 sqlqry
                    GeneralConversation.last_message_at < anonymous_expiry,
                )
            )
            .all()
        )

        for conv in expired_anonymous:
            db.delete(conv)
            cleaned_count += 1

        # Clean up old authenticated general conversations
        auth_expiry = now - self.authenticated_session_expiry
        expired_auth = (
            db.query(GeneralConversation)
            .filter(
                and_(
                    GeneralConversation.is_logged_in == True,  # noqa: E712 sqlqry  
                    GeneralConversation.last_message_at < auth_expiry,
                )
            )
            .all()
        )

        for conv in expired_auth:
            db.delete(conv)
            cleaned_count += 1

        # Property conversations are no longer automatically archived
        # They will remain active until explicitly marked as closed
        # Once closed, they will be kept indefinitely for record-keeping

        try:
            db.commit()
        except Exception as e:
            db.rollback()
            raise Exception(f"Failed to cleanup sessions: {str(e)}")

        return cleaned_count

    def is_session_valid(self, conversation: GeneralConversation) -> bool:
        """Check if a session is still valid based on its type and last activity."""
        if not conversation:
            return False

        now = datetime.utcnow()
        last_activity = conversation.last_message_at

        if conversation.is_logged_in:
            return now - last_activity < self.authenticated_session_expiry
        else:
            return now - last_activity < self.anonymous_session_expiry

    def is_property_session_valid(self, conversation: PropertyConversation) -> bool:
        """Check if a property conversation session is still valid."""
        if not conversation:
            return False

        # Property conversations remain valid indefinitely while active
        return conversation.conversation_status == "active"

    async def refresh_session(self, conversation: GeneralConversation) -> None:
        """Update the last activity timestamp for a session."""
        if conversation:
            conversation.last_message_at = datetime.utcnow()
