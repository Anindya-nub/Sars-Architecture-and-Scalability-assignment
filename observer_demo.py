"""
Task 2.3(d)
Observer pattern implementation for marks update notifications.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List


class MarksObserver(ABC):
    """Observer interface for services interested in marks updates."""

    @abstractmethod
    def update(self, student_id: int, new_marks: float) -> None:
        """React to a marks update event."""
        raise NotImplementedError


class EmailNotifier(MarksObserver):
    """Observer that sends an email when marks are updated."""

    def update(self, student_id: int, new_marks: float) -> None:
        print(
            f"EmailNotifier: Email sent to student {student_id} "
            f"for updated marks {new_marks}."
        )


class AuditLogNotifier(MarksObserver):
    """Observer that records marks update activity in the audit log."""

    def update(self, student_id: int, new_marks: float) -> None:
        print(
            f"AuditLogNotifier: Audit log recorded for student {student_id}; "
            f"new marks = {new_marks}."
        )


class MarksUpdateNotifier:
    """
    Subject in the Observer pattern.

    The Admin Panel can call notify_marks_updated() without knowing the concrete
    details of email sending or audit logging.
    """

    def __init__(self) -> None:
        self._observers: List[MarksObserver] = []

    def register(self, observer: MarksObserver) -> None:
        """Register an observer if it is not already registered."""
        if observer not in self._observers:
            self._observers.append(observer)

    def deregister(self, observer: MarksObserver) -> None:
        """Remove a registered observer."""
        if observer in self._observers:
            self._observers.remove(observer)

    def notify_marks_updated(self, student_id: int, new_marks: float) -> None:
        """Notify all registered observers about a marks update."""
        for observer in self._observers:
            observer.update(student_id, new_marks)


if __name__ == "__main__":
    notifier = MarksUpdateNotifier()
    email_notifier = EmailNotifier()
    audit_log_notifier = AuditLogNotifier()

    notifier.register(email_notifier)
    notifier.register(audit_log_notifier)
    notifier.notify_marks_updated(student_id=1, new_marks=91.0)

    print("--- After deregistering EmailNotifier ---")
    notifier.deregister(email_notifier)
    notifier.notify_marks_updated(student_id=1, new_marks=94.0)
