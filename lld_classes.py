"""
Task 2.3(a) and 2.3(b)
Low-level design classes and repository interface for the SARS Student Portal module.

This file is intentionally framework-independent so it can run as plain Python.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional


class EnrollmentStatus(str, Enum):
    """Allowed enrollment status values."""

    ENROLLED = "ENROLLED"
    WAITLISTED = "WAITLISTED"
    DROPPED = "DROPPED"
    COMPLETED = "COMPLETED"


@dataclass
class Student:
    """
    Represents a student in the Student Portal.

    SOLID decision: Single Responsibility Principle (SRP)
    ----------------------------------------------------
    The Student class stores student data and student-specific behavior only.
    It does not send email notifications. Email notification belongs to a
    separate notification service/class, because sending email is a different
    responsibility from representing a student.
    """

    student_id: int
    student_name: str
    department: str
    advisor_id: int
    email: str
    enrollment_year: int

    def get_profile(self) -> Dict[str, object]:
        """Return a serializable profile dictionary for display in the portal."""
        return {
            "student_id": self.student_id,
            "student_name": self.student_name,
            "department": self.department,
            "advisor_id": self.advisor_id,
            "email": self.email,
            "enrollment_year": self.enrollment_year,
        }

    def update_email(self, new_email: str) -> None:
        """Update the student's contact email after basic validation."""
        if "@" not in new_email:
            raise ValueError("Invalid email address")
        self.email = new_email

    def belongs_to_department(self, department: str) -> bool:
        """Return True when the student belongs to the supplied department."""
        return self.department.lower() == department.lower()


class EnrollmentRepository(ABC):
    """
    Repository interface for enrollment persistence.

    Task 2.3(b): Method signatures only; no database implementation is included.

    SOLID decision: Dependency Inversion Principle (DIP)
    ----------------------------------------------------
    The Enrollment domain class depends on this abstraction instead of depending
    directly on MySQL, PostgreSQL, or any concrete database implementation.
    A concrete SQL repository can implement this interface without forcing
    Enrollment to change.
    """

    @abstractmethod
    def save(self, enrollment: "Enrollment") -> None:
        """Persist an enrollment record."""
        raise NotImplementedError

    @abstractmethod
    def find_by_student_and_course(
        self, student_id: int, course_code: str
    ) -> Optional["Enrollment"]:
        """Return one enrollment by student and course, or None if not found."""
        raise NotImplementedError

    @abstractmethod
    def update_marks(
        self, enrollment_id: int, marks_obtained: float
    ) -> None:
        """Update marks for a specific enrollment."""
        raise NotImplementedError

    @abstractmethod
    def delete(self, enrollment_id: int) -> None:
        """Delete one enrollment record by its primary key."""
        raise NotImplementedError

    @abstractmethod
    def list_by_student(self, student_id: int) -> List["Enrollment"]:
        """Return all enrollments for a student."""
        raise NotImplementedError


@dataclass
class Enrollment:
    """
    Represents a student's enrollment in a course.

    SOLID decision: Open/Closed Principle (OCP)
    -------------------------------------------
    This base class can be extended by subtypes such as WaitlistedEnrollment
    without modifying the base Enrollment class. New behavior is added through
    subclassing and method overriding.
    """

    enrollment_id: int
    student_id: int
    course_code: str
    enrollment_year: int
    status: EnrollmentStatus = EnrollmentStatus.ENROLLED
    marks_obtained: Optional[float] = None

    def assign_marks(self, marks_obtained: float) -> None:
        """Assign marks to an enrollment after validating the allowed range."""
        if marks_obtained < 0 or marks_obtained > 100:
            raise ValueError("Marks must be between 0 and 100")
        self.marks_obtained = marks_obtained
        self.status = EnrollmentStatus.COMPLETED

    def drop(self) -> None:
        """Mark this enrollment as dropped."""
        self.status = EnrollmentStatus.DROPPED

    def is_passed(self) -> bool:
        """Return True when marks are available and at least 35."""
        return self.marks_obtained is not None and self.marks_obtained >= 35

    def can_be_graded(self) -> bool:
        """Return True when this enrollment can receive marks."""
        return self.status in {EnrollmentStatus.ENROLLED, EnrollmentStatus.COMPLETED}

    def save(self, repository: EnrollmentRepository) -> None:
        """
        Save through an EnrollmentRepository abstraction.

        This keeps the domain class independent from a concrete database driver.
        """
        repository.save(self)


@dataclass
class WaitlistedEnrollment(Enrollment):
    """
    Extension of Enrollment for waitlisted students.

    This demonstrates OCP: waitlist behavior is added without editing the
    existing Enrollment class.
    """

    waitlist_position: int = 1
    status: EnrollmentStatus = EnrollmentStatus.WAITLISTED

    def can_be_graded(self) -> bool:
        """Waitlisted students cannot be graded until they are enrolled."""
        return False

    def activate_if_seat_available(self, available_seats: int) -> bool:
        """Convert the waitlisted enrollment to enrolled if a seat is available."""
        if available_seats <= 0:
            return False
        self.status = EnrollmentStatus.ENROLLED
        self.waitlist_position = 0
        return True


if __name__ == "__main__":
    student = Student(
        student_id=1,
        student_name="Asha Nair",
        department="Computer Science",
        advisor_id=101,
        email="asha@example.com",
        enrollment_year=2024,
    )
    enrollment = Enrollment(
        enrollment_id=1001,
        student_id=1,
        course_code="CS101",
        enrollment_year=2024,
    )
    enrollment.assign_marks(88.5)
    print(student.get_profile())
    print(enrollment)
