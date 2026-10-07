-- ============================================================
-- AGENTLAB / NEXUSWORKS
-- 001_schema.sql
--
-- Synthetic enterprise data model for AgentLab
-- PostgreSQL / Supabase
-- ============================================================

-- ------------------------------------------------------------
-- CLEAN START
-- ------------------------------------------------------------

DROP VIEW IF EXISTS v_project_health CASCADE;
DROP VIEW IF EXISTS v_customer_health CASCADE;

DROP TABLE IF EXISTS activities CASCADE;
DROP TABLE IF EXISTS meetings CASCADE;
DROP TABLE IF EXISTS documents CASCADE;
DROP TABLE IF EXISTS tickets CASCADE;
DROP TABLE IF EXISTS invoices CASCADE;
DROP TABLE IF EXISTS contracts CASCADE;
DROP TABLE IF EXISTS project_members CASCADE;
DROP TABLE IF EXISTS projects CASCADE;
DROP TABLE IF EXISTS vendors CASCADE;
DROP TABLE IF EXISTS contacts CASCADE;
DROP TABLE IF EXISTS employees CASCADE;
DROP TABLE IF EXISTS customers CASCADE;


-- ============================================================
-- CUSTOMERS
-- ============================================================

CREATE TABLE customers (
    customer_id         TEXT PRIMARY KEY,
    customer_code       TEXT UNIQUE NOT NULL,
    company_name        TEXT NOT NULL,
    industry            TEXT NOT NULL,
    company_size        TEXT NOT NULL,
    region              TEXT NOT NULL,
    country             TEXT NOT NULL DEFAULT 'USA',
    account_tier        TEXT NOT NULL,
    annual_revenue      NUMERIC(15,2),
    account_status      TEXT NOT NULL DEFAULT 'Active',
    customer_since      DATE NOT NULL,
    primary_account_manager_id TEXT,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CHECK (account_status IN ('Active', 'At Risk', 'Inactive', 'Prospect')),
    CHECK (account_tier IN ('Strategic', 'Enterprise', 'Mid-Market', 'SMB'))
);


-- ============================================================
-- EMPLOYEES
-- ============================================================

CREATE TABLE employees (
    employee_id         TEXT PRIMARY KEY,
    employee_code       TEXT UNIQUE NOT NULL,
    first_name          TEXT NOT NULL,
    last_name           TEXT NOT NULL,
    full_name            TEXT NOT NULL,
    email               TEXT UNIQUE NOT NULL,
    department          TEXT NOT NULL,
    job_title           TEXT NOT NULL,
    seniority           TEXT NOT NULL,
    region              TEXT NOT NULL,
    manager_id          TEXT REFERENCES employees(employee_id),
    hire_date           DATE NOT NULL,
    employment_status   TEXT NOT NULL DEFAULT 'Active',
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CHECK (employment_status IN ('Active', 'On Leave', 'Inactive'))
);


-- ============================================================
-- CONTACTS
-- ============================================================

CREATE TABLE contacts (
    contact_id          TEXT PRIMARY KEY,
    customer_id         TEXT NOT NULL REFERENCES customers(customer_id),
    first_name          TEXT NOT NULL,
    last_name           TEXT NOT NULL,
    full_name            TEXT NOT NULL,
    email               TEXT NOT NULL,
    job_title           TEXT,
    department          TEXT,
    seniority           TEXT,
    contact_role        TEXT,
    is_primary          BOOLEAN NOT NULL DEFAULT FALSE,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);


-- ============================================================
-- VENDORS
-- ============================================================

CREATE TABLE vendors (
    vendor_id           TEXT PRIMARY KEY,
    vendor_code         TEXT UNIQUE NOT NULL,
    vendor_name         TEXT NOT NULL,
    vendor_category     TEXT NOT NULL,
    region              TEXT NOT NULL,
    risk_level          TEXT NOT NULL,
    account_status      TEXT NOT NULL DEFAULT 'Active',
    annual_spend        NUMERIC(15,2),
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CHECK (risk_level IN ('Low', 'Medium', 'High', 'Critical')),
    CHECK (account_status IN ('Active', 'Inactive', 'Under Review'))
);


-- ============================================================
-- PROJECTS
-- ============================================================

CREATE TABLE projects (
    project_id              TEXT PRIMARY KEY,
    project_code            TEXT UNIQUE NOT NULL,
    customer_id             TEXT NOT NULL REFERENCES customers(customer_id),
    project_name            TEXT NOT NULL,
    project_type            TEXT NOT NULL,
    description             TEXT,
    project_status          TEXT NOT NULL,
    health_status           TEXT NOT NULL,
    priority                TEXT NOT NULL,
    project_manager_id      TEXT REFERENCES employees(employee_id),
    technical_lead_id       TEXT REFERENCES employees(employee_id),
    account_manager_id      TEXT REFERENCES employees(employee_id),
    start_date              DATE NOT NULL,
    planned_end_date        DATE NOT NULL,
    actual_end_date         DATE,
    budget                  NUMERIC(15,2) NOT NULL,
    actual_spend            NUMERIC(15,2) NOT NULL DEFAULT 0,
    completion_percent      NUMERIC(5,2) NOT NULL DEFAULT 0,
    created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CHECK (project_status IN (
        'Planned',
        'Active',
        'On Hold',
        'Completed',
        'Cancelled'
    )),

    CHECK (health_status IN (
        'On Track',
        'At Risk',
        'Delayed',
        'Critical'
    )),

    CHECK (priority IN ('Low', 'Medium', 'High', 'Critical'))
);


-- ============================================================
-- PROJECT MEMBERS
-- ============================================================

CREATE TABLE project_members (
    project_member_id   BIGSERIAL PRIMARY KEY,
    project_id          TEXT NOT NULL REFERENCES projects(project_id) ON DELETE CASCADE,
    employee_id         TEXT NOT NULL REFERENCES employees(employee_id),
    role                TEXT NOT NULL,
    allocation_percent  NUMERIC(5,2) NOT NULL DEFAULT 25,
    joined_date         DATE NOT NULL,
    left_date           DATE,
    is_active           BOOLEAN NOT NULL DEFAULT TRUE,

    UNIQUE(project_id, employee_id)
);


-- ============================================================
-- CONTRACTS
-- ============================================================

CREATE TABLE contracts (
    contract_id         TEXT PRIMARY KEY,
    contract_number     TEXT UNIQUE NOT NULL,
    customer_id         TEXT REFERENCES customers(customer_id),
    vendor_id           TEXT REFERENCES vendors(vendor_id),
    project_id          TEXT REFERENCES projects(project_id),
    contract_type       TEXT NOT NULL,
    contract_status     TEXT NOT NULL,
    start_date          DATE NOT NULL,
    end_date            DATE NOT NULL,
    contract_value      NUMERIC(15,2) NOT NULL,
    renewal_type        TEXT,
    owner_employee_id   TEXT REFERENCES employees(employee_id),
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);


-- ============================================================
-- INVOICES
-- ============================================================

CREATE TABLE invoices (
    invoice_id          TEXT PRIMARY KEY,
    invoice_number      TEXT UNIQUE NOT NULL,
    customer_id         TEXT NOT NULL REFERENCES customers(customer_id),
    project_id          TEXT REFERENCES projects(project_id),
    invoice_date        DATE NOT NULL,
    due_date            DATE NOT NULL,
    amount              NUMERIC(15,2) NOT NULL,
    currency            TEXT NOT NULL DEFAULT 'USD',
    status              TEXT NOT NULL,
    payment_date        DATE,
    payment_method      TEXT,
    description         TEXT,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CHECK (status IN (
        'Draft',
        'Pending',
        'Paid',
        'Partially Paid',
        'Overdue',
        'Disputed',
        'Cancelled'
    ))
);


-- ============================================================
-- TICKETS
-- ============================================================

CREATE TABLE tickets (
    ticket_id           TEXT PRIMARY KEY,
    ticket_number       TEXT UNIQUE NOT NULL,
    project_id          TEXT NOT NULL REFERENCES projects(project_id),
    customer_id         TEXT NOT NULL REFERENCES customers(customer_id),
    title               TEXT NOT NULL,
    description         TEXT,
    category            TEXT NOT NULL,
    severity            TEXT NOT NULL,
    status              TEXT NOT NULL,
    priority            TEXT NOT NULL,
    assigned_to         TEXT REFERENCES employees(employee_id),
    reported_by_contact TEXT REFERENCES contacts(contact_id),
    created_at          TIMESTAMPTZ NOT NULL,
    resolved_at         TIMESTAMPTZ,
    sla_due_at          TIMESTAMPTZ,
    root_cause          TEXT,

    CHECK (severity IN ('Low', 'Medium', 'High', 'Critical')),
    CHECK (status IN (
        'Open',
        'In Progress',
        'Blocked',
        'Resolved',
        'Closed'
    )),
    CHECK (priority IN ('Low', 'Medium', 'High', 'Critical'))
);


-- ============================================================
-- DOCUMENTS
-- ============================================================

CREATE TABLE documents (
    document_id         TEXT PRIMARY KEY,
    document_number     TEXT UNIQUE NOT NULL,
    project_id          TEXT REFERENCES projects(project_id),
    customer_id         TEXT REFERENCES customers(customer_id),
    document_type       TEXT NOT NULL,
    title               TEXT NOT NULL,
    summary             TEXT,
    document_status     TEXT NOT NULL,
    author_employee_id  TEXT REFERENCES employees(employee_id),
    created_at          TIMESTAMPTZ NOT NULL,
    updated_at          TIMESTAMPTZ NOT NULL,
    content             TEXT,

    CHECK (document_status IN (
        'Draft',
        'Final',
        'Archived',
        'Under Review'
    ))
);


-- ============================================================
-- MEETINGS
-- ============================================================

CREATE TABLE meetings (
    meeting_id          TEXT PRIMARY KEY,
    project_id          TEXT REFERENCES projects(project_id),
    customer_id         TEXT REFERENCES customers(customer_id),
    meeting_type        TEXT NOT NULL,
    title               TEXT NOT NULL,
    scheduled_at        TIMESTAMPTZ NOT NULL,
    duration_minutes    INTEGER NOT NULL,
    organizer_id        TEXT REFERENCES employees(employee_id),
    summary             TEXT,
    decisions            TEXT,
    action_items        TEXT,
    next_meeting_date   DATE,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);


-- ============================================================
-- ACTIVITIES
-- ============================================================

CREATE TABLE activities (
    activity_id         BIGSERIAL PRIMARY KEY,
    customer_id         TEXT REFERENCES customers(customer_id),
    project_id          TEXT REFERENCES projects(project_id),
    employee_id         TEXT REFERENCES employees(employee_id),
    activity_type       TEXT NOT NULL,
    subject             TEXT NOT NULL,
    description         TEXT,
    activity_status     TEXT,
    occurred_at         TIMESTAMPTZ NOT NULL
);


-- ============================================================
-- INDEXES
-- ============================================================

CREATE INDEX idx_contacts_customer
    ON contacts(customer_id);

CREATE INDEX idx_projects_customer
    ON projects(customer_id);

CREATE INDEX idx_projects_pm
    ON projects(project_manager_id);

CREATE INDEX idx_projects_account_manager
    ON projects(account_manager_id);

CREATE INDEX idx_project_members_project
    ON project_members(project_id);

CREATE INDEX idx_project_members_employee
    ON project_members(employee_id);

CREATE INDEX idx_contracts_customer
    ON contracts(customer_id);

CREATE INDEX idx_contracts_project
    ON contracts(project_id);

CREATE INDEX idx_contracts_vendor
    ON contracts(vendor_id);

CREATE INDEX idx_invoices_customer
    ON invoices(customer_id);

CREATE INDEX idx_invoices_project
    ON invoices(project_id);

CREATE INDEX idx_invoices_status
    ON invoices(status);

CREATE INDEX idx_invoices_due_date
    ON invoices(due_date);

CREATE INDEX idx_tickets_project
    ON tickets(project_id);

CREATE INDEX idx_tickets_customer
    ON tickets(customer_id);

CREATE INDEX idx_tickets_status
    ON tickets(status);

CREATE INDEX idx_tickets_severity
    ON tickets(severity);

CREATE INDEX idx_documents_project
    ON documents(project_id);

CREATE INDEX idx_documents_customer
    ON documents(customer_id);

CREATE INDEX idx_meetings_project
    ON meetings(project_id);

CREATE INDEX idx_meetings_customer
    ON meetings(customer_id);

CREATE INDEX idx_activities_project
    ON activities(project_id);

CREATE INDEX idx_activities_customer
    ON activities(customer_id);

CREATE INDEX idx_activities_occurred
    ON activities(occurred_at);


-- ============================================================
-- HELPFUL AGENTLAB VIEWS
-- ============================================================

CREATE VIEW v_project_health AS
SELECT
    p.project_id,
    p.project_code,
    p.project_name,
    c.company_name AS customer_name,
    p.project_status,
    p.health_status,
    p.priority,
    p.budget,
    p.actual_spend,
    p.completion_percent,

    COUNT(DISTINCT t.ticket_id)
        FILTER (WHERE t.ticket_id IS NOT NULL) AS ticket_count,

    COUNT(DISTINCT t.ticket_id)
        FILTER (WHERE t.severity = 'Critical'
                 AND t.status NOT IN ('Resolved', 'Closed')) AS critical_ticket_count,

    COUNT(DISTINCT t.ticket_id)
        FILTER (WHERE t.status = 'Blocked') AS blocked_ticket_count,

    COUNT(DISTINCT i.invoice_id)
        FILTER (WHERE i.status = 'Overdue') AS overdue_invoice_count,

    COALESCE(
        SUM(i.amount) FILTER (WHERE i.status = 'Overdue'),
        0
    ) AS overdue_invoice_amount

FROM projects p
JOIN customers c
    ON c.customer_id = p.customer_id
LEFT JOIN tickets t
    ON t.project_id = p.project_id
LEFT JOIN invoices i
    ON i.project_id = p.project_id
GROUP BY
    p.project_id,
    p.project_code,
    p.project_name,
    c.company_name,
    p.project_status,
    p.health_status,
    p.priority,
    p.budget,
    p.actual_spend,
    p.completion_percent;


CREATE VIEW v_customer_health AS
SELECT
    c.customer_id,
    c.company_name,
    c.industry,
    c.account_tier,

    COUNT(DISTINCT p.project_id) AS project_count,

    COUNT(DISTINCT p.project_id)
        FILTER (WHERE p.health_status IN ('At Risk', 'Delayed', 'Critical'))
        AS risky_project_count,

    COUNT(DISTINCT i.invoice_id)
        FILTER (WHERE i.status = 'Overdue')
        AS overdue_invoice_count,

    COALESCE(
        SUM(i.amount) FILTER (WHERE i.status = 'Overdue'),
        0
    ) AS overdue_invoice_amount,

    COUNT(DISTINCT t.ticket_id)
        FILTER (
            WHERE t.severity = 'Critical'
            AND t.status NOT IN ('Resolved', 'Closed')
        ) AS open_critical_ticket_count

FROM customers c
LEFT JOIN projects p
    ON p.customer_id = c.customer_id
LEFT JOIN invoices i
    ON i.customer_id = c.customer_id
LEFT JOIN tickets t
    ON t.customer_id = c.customer_id
GROUP BY
    c.customer_id,
    c.company_name,
    c.industry,
    c.account_tier;


-- ============================================================
-- DONE
-- ============================================================

SELECT
    'Schema created successfully' AS message;