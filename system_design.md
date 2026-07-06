# SARS System Design: Architecture and Scalability

## Task 2.1 — Requirements and Architecture Choice

### 2.1(a) Functional and non-functional requirements

#### Functional requirements

1. **Authentication**
   - Students, faculty, and administrators must be able to log in securely using their credentials.
   - The system must enforce role-based access so students, faculty, and admins can access only the features allowed for their role.

2. **Student Portal**
   - Students must be able to view their marks, enrolled courses, department details, and advisor details.
   - Students must be able to enroll in available courses if they satisfy the required rules.

3. **Admin Panel**
   - Administrators must be able to create, update, and delete student records, course records, faculty records, marks, and enrollment records.
   - Marks updates should trigger notifications and audit logging.

#### Non-functional requirements

| Non-functional requirement | Description | Primary design principle addressed |
|---|---|---|
| High concurrent user handling | SARS must handle 50,000 concurrent users during result publication. | Scalability |
| High uptime during result publication | SARS should remain available even if one server or service fails. | Availability |
| Secure access and data protection | Authentication, authorization, password hashing, HTTPS, and role-based access control must protect student and marks data. | Security |

### 2.1(b) Monolithic architecture vs microservices architecture

| Dimension | Monolithic architecture | Microservices architecture |
|---|---|---|
| Independent deployment | All modules are usually deployed together as one application. A small change in one module may require redeploying the entire system. | Each service can be deployed independently, such as Authentication, Student Portal, Admin Panel, Email, and Audit services. |
| Fault isolation | A major failure in one module can affect the entire application because all modules run inside the same deployable unit. | Failure can be isolated to one service. For example, Email Service failure should not stop students from viewing marks. |
| Management complexity | Easier to develop, test, deploy, and monitor initially because there is one codebase and one deployment unit. | More complex because it requires service discovery, inter-service communication, distributed logging, monitoring, and version management. |

#### Recommended architecture for SARS

For SARS at the expected scale of **50,000 concurrent users**, a **microservices architecture** is recommended. The main reason is that the Authentication, Student Portal, Admin Panel, Email Notification, and Audit Log responsibilities can scale and fail independently. During result publication, the Student Portal may need far more instances than the Admin Panel, so independent scaling is useful. The trade-off is higher operational complexity, but that complexity is justified because availability, fault isolation, and independent scaling are more important at this public-facing scale.

---

## Task 2.2 — High-Level Design

### 2.2(a) Main components of SARS

| Component | Single responsibility | Interface exposed |
|---|---|---|
| Web Frontend | Provides the browser-based UI for login, student portal, and admin panel screens. | HTTPS web interface; calls backend REST APIs. |
| API Gateway / Load Balancer | Receives client requests, terminates HTTPS if configured, and routes requests to backend services. | Public HTTPS endpoint; internal HTTP/REST routing. |
| Authentication Service | Handles login, logout, password validation, token/session generation, and role-based access checks. | REST API, for example `/login`, `/logout`, `/validate-token`. |
| Student Portal Service | Allows students to view marks, view enrolled courses, and request course enrollment. | REST API, for example `/students/{id}/marks`, `/students/{id}/enrollments`. |
| Admin Panel Service | Allows admins to manage students, courses, faculty, departments, enrollments, and marks. | REST API, for example `/admin/students`, `/admin/courses`, `/admin/marks`. |
| Course Service | Maintains course details, instructor mapping, course capacity, and course availability. | REST API or internal service API. |
| Marks Service | Stores and retrieves marks, calculates grade-related summaries, and provides result data. | REST API or internal service API. |
| Email Notification Service | Sends emails after events such as marks update, enrollment confirmation, and password reset. | REST API or message-based interface. |
| Audit Log Service | Records sensitive actions such as admin marks updates, login attempts, and student data changes. | REST API or message-based interface. |
| Database Tier | Persists students, courses, enrollments, marks, users, roles, and audit records. | SQL query interface used by backend services through repositories/DAOs. |
| Cache / Shared Session Store | Stores frequently accessed result data or shared session data to reduce database load. | Key-value interface. |

### 2.2(b) Layered architecture for Student Portal module

The Student Portal module can be structured into three main layers.

#### 1. Presentation layer

**Responsibility:**
- Displays the student dashboard, marks page, enrolled courses page, and course enrollment form.
- Collects user actions such as clicking “View Marks” or “Enroll in Course”.
- Performs basic client-side validation such as required fields and display formatting.

**Receives:**
- Browser requests and student input.
- Authentication token/session information from the browser.

**Passes on:**
- Clean API requests to the Student Portal backend, such as `GET /students/{student_id}/marks` or `POST /students/{student_id}/enrollments`.

#### 2. Business layer

**Responsibility:**
- Applies application rules.
- Checks whether the logged-in student is allowed to access the requested student record.
- Validates enrollment rules, such as course availability, duplicate enrollment prevention, and course capacity.
- Coordinates with Course Service, Marks Service, and database repositories.

**Receives:**
- Validated API requests from the presentation/API controller layer.
- Student identity and role information from the Authentication Service.

**Passes on:**
- Repository calls to the data access layer.
- Response objects such as marks summaries, enrollment confirmation, or validation error messages.

#### 3. Data access layer

**Responsibility:**
- Performs database operations for students, marks, courses, and enrollments.
- Converts database rows into domain objects or response DTOs.
- Keeps SQL queries and persistence logic separate from business rules.

**Receives:**
- Repository method calls from the business layer, such as `find_marks_by_student_id(student_id)` or `create_enrollment(student_id, course_code)`.

**Passes on:**
- SQL queries to the database.
- Database results back to the business layer as structured objects.

### 2.2(c) Scaling strategy and load balancing

For SARS web servers, **horizontal scaling** should be used instead of only vertical scaling.

Horizontal scaling means running multiple web server instances and distributing traffic across them. This is more suitable for 50,000 concurrent users because additional servers can be added during peak demand, and the system does not depend on a single large machine. Vertical scaling, such as increasing CPU and RAM on one server, has hardware limits and still leaves the system more exposed to a single-server failure.

A load balancer should distribute incoming requests across multiple web servers. One suitable algorithm is **round-robin**, where requests are assigned to servers in sequence: Server A, then Server B, then Server C, and then back to Server A. Round-robin is suitable when the web servers are similar in capacity and the requests are relatively similar in processing cost, such as many students viewing result pages.

### 2.2(d) Elasticity and cost reduction

Elasticity allows SARS to automatically increase or decrease the number of running server instances based on demand. During result publication, more web server and backend service instances can be started to handle the peak load. During semester breaks or normal low-traffic periods, unnecessary instances can be stopped or scaled down. This reduces cost because the university pays for high capacity only when it is needed, instead of permanently running peak-level infrastructure.

### 2.2(e) Session-routing problem with round-robin load balancing

If Server A creates an in-memory session during login and the next request goes to Server B, Server B may not recognize the user. The student may appear logged out even though the login succeeded. This problem is called the **session affinity problem**, also known as the **sticky session problem** or **server-local session state problem**.

#### Strategy 1: Routing-based solution — sticky sessions

The load balancer can use **sticky sessions**, where all requests from the same authenticated user are routed to the same server that created the session.

**How it works:**
- The load balancer stores a routing decision using a cookie, session ID, or client IP hash.
- If a student logs in through Server A, later requests from that student are routed back to Server A.

**Trade-off:**
- Load distribution becomes less even because some servers may receive more long-lived sessions than others.
- Fault tolerance is weaker because if Server A fails, all sessions stored only on Server A may be lost.

#### Strategy 2: Storage-based solution — shared session store

Sessions can be stored outside individual web servers in a shared session store, such as a database or distributed cache.

**How it works:**
- Server A creates the session in the shared store.
- Server B can validate the same session by reading it from the shared store.
- Any web server can handle any request.

**Trade-off:**
- This improves fault tolerance and load distribution, but adds extra infrastructure cost and network latency.
- The shared session store must also be highly available, otherwise it can become a new bottleneck or single point of failure.
