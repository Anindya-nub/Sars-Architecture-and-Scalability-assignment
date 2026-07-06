# SARS System Design Assignment

This repository contains the submission files for Part 2: Software System Design, Architecture, Scalability, Low-Level Design, SOLID Principles, Singleton Pattern, Observer Pattern, Redundancy, and Fault Tolerance.

## Repository contents

| File | Purpose |
|---|---|
| `system_design.md` | Written answers for Task 2.1 and Task 2.2. |
| `lld_classes.py` | Student class, Enrollment class, WaitlistedEnrollment extension, and EnrollmentRepository interface for Task 2.3(a) and Task 2.3(b). |
| `singleton_demo.py` | Thread-safe Singleton implementation for Task 2.3(c). |
| `observer_demo.py` | Observer pattern implementation for Task 2.3(d). |
| `README.md` | Explanation of architecture decisions, SOLID application, Observer rationale, redundancy, fault tolerance, and replication trade-offs. |

---

## Architecture decision summary

SARS is expected to serve 50,000 concurrent users during examination result publication. Because the application has separate major responsibilities — Authentication, Student Portal, Admin Panel, Email Notification, and Audit Logging — a microservices architecture is recommended.

The main reasons are:

1. **Independent scaling**: The Student Portal can be scaled heavily during result publication without scaling the Admin Panel equally.
2. **Independent deployment**: Changes to the Email Service or Audit Log Service do not require redeploying the entire application.
3. **Fault isolation**: If the Email Notification service fails, the Student Portal can still allow students to view marks and enroll in courses.

The trade-off is that microservices are harder to manage than a monolith. They require better monitoring, logging, API versioning, deployment automation, and failure handling. For this scale, the reliability and scalability benefits justify the extra complexity.

---

## SOLID application in the low-level design

### 1. Single Responsibility Principle

The `Student` class in `lld_classes.py` only represents student data and student-specific behavior. It does not contain methods for sending email notifications. Email notification is handled separately by observer classes in `observer_demo.py`.

This avoids mixing unrelated responsibilities. Changing the email delivery mechanism should not require changing the `Student` class.

### 2. Open/Closed Principle

The `Enrollment` class is open for extension but closed for modification. The file includes a `WaitlistedEnrollment` subclass that adds waitlist-specific behavior without modifying the base `Enrollment` class.

This means future enrollment types, such as `AuditOnlyEnrollment` or `DeferredEnrollment`, can be added as new subclasses instead of repeatedly editing the original class.

### 3. Dependency Inversion Principle

The `Enrollment` class saves itself through the `EnrollmentRepository` abstraction. It does not depend on PostgreSQL, MySQL, or a concrete database driver.

A concrete repository can later implement `EnrollmentRepository` using SQL, an ORM, or a test in-memory store. The domain class remains stable because it depends on an interface, not a low-level implementation.

---

## Singleton pattern rationale

The `singleton_demo.py` file implements a thread-safe Singleton for `DatabaseConnection`.

The class uses:

- a class-level `_instance` variable,
- a class-level `threading.Lock`,
- double-checked locking inside `__new__`, and
- a `get_connection()` method that returns the shared connection object.

Naive lazy initialization is unsafe under concurrent access. Two threads may both check `_instance is None` at nearly the same time and both create separate objects. The lock prevents this race condition, and the second check inside the lock ensures only one instance is created.

---

## Observer pattern rationale

The `observer_demo.py` file implements the Observer pattern using:

- `MarksUpdateNotifier` as the subject,
- `EmailNotifier` as one observer, and
- `AuditLogNotifier` as another observer.

The Admin Panel only needs to notify the subject that marks were updated. It does not need to know the internal details of email sending or audit logging. This keeps the Admin Panel loosely coupled from notification services.

The implementation supports:

- registering observers,
- notifying all observers, and
- deregistering observers.

This makes the design flexible. For example, an SMS observer or analytics observer could be added later without modifying the Admin Panel's marks update logic.

---

## Task 2.4 — Redundancy and Fault Tolerance

### 2.4(a) Database-tier redundancy

SARS should replicate data across multiple database servers to avoid data loss and reduce downtime. A common design is a primary-replica database setup.

- The **primary database** handles write requests such as marks updates, enrollment creation, and student record changes.
- The **replica database** maintains a copy of the primary's data.
- Read-heavy operations, such as viewing marks during result publication, can be directed to replicas when the consistency requirements allow it.

If the primary database fails, a replica can be promoted to become the new primary. After failover, write requests are redirected to the newly promoted primary. Read requests can continue from available replicas. This improves availability because the system does not depend on one database server.

### 2.4(b) Fault isolation between Student Portal and Email Service

The specific microservices property that makes this possible is **fault isolation**.

Because the Student Portal and Email Notification service are independently deployed services, a crash in the Email Service does not need to crash the Student Portal. Students should still be able to view marks and enroll in courses even if email notifications temporarily fail.

In a monolithic design, the same failure could bring down the entire application if the email code runs inside the same process and throws an unhandled exception or blocks the request thread. Since all modules are packaged together in one application, a severe failure in one internal module can affect unrelated features.

The Student Portal's code must avoid letting the email failure propagate into the marks-display or enrollment path. At the call site, it should wrap the notification call separately, catch notification errors, log the failure, and still return success for the main student action if the marks display or enrollment operation itself succeeded.

Example call-site pattern in plain logic:

```text
update marks or create enrollment
commit the main student/admin transaction
try to send notification
    if notification succeeds, continue normally
catch notification error
    log the error for retry or admin review
    do not fail the marks-display or enrollment response
return success for the main operation
```

This prevents a non-critical notification failure from becoming a critical Student Portal failure.

### 2.4(c) Synchronous primary-replica replication trade-off

In synchronous primary-replica replication, every write must be sent to the replica and acknowledged by the replica before the primary confirms success to the application.

The trade-off is:

- **Synchronous replication has higher write latency** because the primary must wait for the replica acknowledgment.
- **Asynchronous replication has lower write latency** because the primary can confirm the write before the replica receives it.
- However, asynchronous replication has a higher risk of replica lag and possible data loss during failover.

If the primary crashes before the replica has received the last committed transaction, the following happens:

1. **Replica state at failover**
   - The replica contains the latest transactions it successfully received and applied.
   - It may be missing the last transaction or transactions that existed on the primary but did not reach the replica.
   - In strict synchronous replication, acknowledged writes should have zero replica lag. Therefore, any missing transaction is usually a transaction that was not safely acknowledged to the application, or it must be recovered from the crashed primary's log.

2. **What the student sees from the newly promoted replica**
   - The student sees the last consistent state available on the promoted replica.
   - If the most recent marks update was not replicated before the crash, the student may see the older marks value.

3. **DBA action before declaring the system fully consistent**
   - The DBA must check the crashed primary's write-ahead log or binary log.
   - If the missing transactions are available, the DBA should apply/replay them to the promoted replica.
   - If the logs are not available, the DBA must acknowledge the data gap, accept the last known consistent replica state, and document the small data loss before declaring the system fully consistent.

---

## How to run the Python files

```bash
python lld_classes.py
python singleton_demo.py
python observer_demo.py
```

Expected behavior:

- `lld_classes.py` prints a sample student profile and enrollment object.
- `singleton_demo.py` prints that only one unique `DatabaseConnection` instance was created.
- `observer_demo.py` prints notification messages, then demonstrates deregistration of the email observer.
