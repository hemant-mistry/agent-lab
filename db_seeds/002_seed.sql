-- ============================================================
-- AGENTLAB / NEXUSWORKS
-- 002_seed.sql
--
-- Synthetic enterprise data generator
-- ============================================================

-- ------------------------------------------------------------
-- Deterministic randomness
-- ------------------------------------------------------------

SELECT setseed(0.424242);


-- ============================================================
-- CONSTANT DATA
-- ============================================================

-- ------------------------------------------------------------
-- Customers
-- ------------------------------------------------------------

INSERT INTO customers (
    customer_id,
    customer_code,
    company_name,
    industry,
    company_size,
    region,
    country,
    account_tier,
    annual_revenue,
    account_status,
    customer_since
)
SELECT
    'C' || LPAD(gs::TEXT, 4, '0'),
    'CUST-' || LPAD(gs::TEXT, 4, '0'),

    (
        ARRAY[
            'Acme','Globex','Stark','Wayne','Umbrella',
            'Initech','Cyberdyne','Wonka','Hooli','Tyrell',
            'Soylent','Massive Dynamic','Vandelay','Oceanic',
            'Prestige','Aperture','LexCorp','Gringotts',
            'Duff','Nakatomi'
        ]
    )[1 + ((gs - 1) % 20)]
    || ' ' ||
    CASE
        WHEN gs % 5 = 0 THEN 'Holdings'
        WHEN gs % 4 = 0 THEN 'Industries'
        WHEN gs % 3 = 0 THEN 'Systems'
        WHEN gs % 2 = 0 THEN 'Corporation'
        ELSE 'Technologies'
    END
    || CASE
        WHEN gs > 20 THEN ' ' || CEIL(gs / 20.0)::INT
        ELSE ''
    END,

    (
        ARRAY[
            'Technology',
            'Financial Services',
            'Healthcare',
            'Manufacturing',
            'Retail',
            'Logistics',
            'Pharmaceuticals',
            'Energy',
            'Telecommunications',
            'Automotive'
        ]
    )[1 + ((gs - 1) % 10)],

    (
        ARRAY[
            'Enterprise',
            'Large',
            'Mid-Market',
            'Small'
        ]
    )[1 + ((gs - 1) % 4)],

    (
        ARRAY[
            'North America',
            'Europe',
            'Asia Pacific',
            'Middle East',
            'Latin America'
        ]
    )[1 + ((gs - 1) % 5)],

    CASE
        WHEN gs % 5 = 0 THEN 'UK'
        WHEN gs % 4 = 0 THEN 'Germany'
        WHEN gs % 3 = 0 THEN 'India'
        ELSE 'USA'
    END,

    CASE
        WHEN gs <= 10 THEN 'Strategic'
        WHEN gs <= 40 THEN 'Enterprise'
        WHEN gs <= 80 THEN 'Mid-Market'
        ELSE 'SMB'
    END,

    ROUND(
        (5000000 + random() * 495000000)::NUMERIC,
        2
    ),

    CASE
        WHEN gs IN (17, 43, 71, 88) THEN 'At Risk'
        WHEN gs IN (99, 100) THEN 'Inactive'
        ELSE 'Active'
    END,

    DATE '2018-01-01'
        + ((random() * 2800)::INT)
FROM generate_series(1, 100) gs;


-- ============================================================
-- EMPLOYEES
-- ============================================================

INSERT INTO employees (
    employee_id,
    employee_code,
    first_name,
    last_name,
    full_name,
    email,
    department,
    job_title,
    seniority,
    region,
    hire_date
)
SELECT
    'E' || LPAD(gs::TEXT, 4, '0'),
    'EMP-' || LPAD(gs::TEXT, 4, '0'),

    (
        ARRAY[
            'Sarah','David','Priya','Michael','Arjun',
            'Elena','Daniel','Rachel','James','Anita',
            'Robert','Sophia','Vikram','Emma','Noah',
            'Olivia','Ethan','Maya','Lucas','Ava'
        ]
    )[1 + ((gs - 1) % 20)],

    (
        ARRAY[
            'Chen','Miller','Shah','Wong','Rao',
            'Garcia','Smith','Johnson','Brown','Patel',
            'Wilson','Anderson','Kumar','Thomas','Martin',
            'Lee','Clark','Lewis','Walker','Hall'
        ]
    )[1 + ((gs - 1) % 20)],

    (
        ARRAY[
            'Sarah','David','Priya','Michael','Arjun',
            'Elena','Daniel','Rachel','James','Anita',
            'Robert','Sophia','Vikram','Emma','Noah',
            'Olivia','Ethan','Maya','Lucas','Ava'
        ]
    )[1 + ((gs - 1) % 20)]
    || ' ' ||
    (
        ARRAY[
            'Chen','Miller','Shah','Wong','Rao',
            'Garcia','Smith','Johnson','Brown','Patel',
            'Wilson','Anderson','Kumar','Thomas','Martin',
            'Lee','Clark','Lewis','Walker','Hall'
        ]
    )[1 + ((gs - 1) % 20)],

    LOWER(
        (
            ARRAY[
                'Sarah','David','Priya','Michael','Arjun',
                'Elena','Daniel','Rachel','James','Anita',
                'Robert','Sophia','Vikram','Emma','Noah',
                'Olivia','Ethan','Maya','Lucas','Ava'
            ]
        )[1 + ((gs - 1) % 20)]
        || '.' ||
        (
            ARRAY[
                'Chen','Miller','Shah','Wong','Rao',
                'Garcia','Smith','Johnson','Brown','Patel',
                'Wilson','Anderson','Kumar','Thomas','Martin',
                'Lee','Clark','Lewis','Walker','Hall'
            ]
        )[1 + ((gs - 1) % 20)]
        || gs
        || '@nexusworks.example'
    ),

    (
        ARRAY[
            'Sales',
            'Delivery',
            'Engineering',
            'Finance',
            'Operations',
            'Product',
            'Legal',
            'Customer Success',
            'Security',
            'Human Resources'
        ]
    )[1 + ((gs - 1) % 10)],

    (
        ARRAY[
            'Account Manager',
            'Project Manager',
            'Solutions Architect',
            'Software Engineer',
            'Technical Program Manager',
            'Finance Manager',
            'Product Manager',
            'Customer Success Manager',
            'Security Engineer',
            'Business Analyst'
        ]
    )[1 + ((gs - 1) % 10)],

    CASE
        WHEN gs <= 20 THEN 'Executive'
        WHEN gs <= 70 THEN 'Senior'
        WHEN gs <= 170 THEN 'Mid'
        ELSE 'Junior'
    END,

    (
        ARRAY[
            'North America',
            'Europe',
            'Asia Pacific',
            'India'
        ]
    )[1 + ((gs - 1) % 4)],

    DATE '2017-01-01'
        + ((random() * 3300)::INT)
FROM generate_series(1, 250) gs;


-- ------------------------------------------------------------
-- Employee managers
-- ------------------------------------------------------------

UPDATE employees e
SET manager_id =
    CASE
        WHEN e.employee_id::TEXT = 'E0001' THEN NULL
        ELSE
            'E' ||
            LPAD(
                (1 + ((substring(e.employee_id from 2)::INT - 1) % 20))::TEXT,
                4,
                '0'
            )
    END;


-- ============================================================
-- CONTACTS
-- ============================================================

INSERT INTO contacts (
    contact_id,
    customer_id,
    first_name,
    last_name,
    full_name,
    email,
    job_title,
    department,
    seniority,
    contact_role,
    is_primary
)
SELECT
    'CT' || LPAD(gs::TEXT, 5, '0'),

    'C' || LPAD(
        (((gs - 1) % 100) + 1)::TEXT,
        4,
        '0'
    ),

    (
        ARRAY[
            'Alex','Jordan','Taylor','Morgan','Chris',
            'Jamie','Casey','Riley','Cameron','Drew',
            'Sam','Avery','Parker','Quinn','Reese'
        ]
    )[1 + ((gs - 1) % 15)],

    (
        ARRAY[
            'Adams','Baker','Carter','Davis','Evans',
            'Foster','Green','Harris','Irwin','Jackson',
            'King','Long','Moore','Nelson','Owens'
        ]
    )[1 + ((gs - 1) % 15)],

    (
        ARRAY[
            'Alex','Jordan','Taylor','Morgan','Chris',
            'Jamie','Casey','Riley','Cameron','Drew',
            'Sam','Avery','Parker','Quinn','Reese'
        ]
    )[1 + ((gs - 1) % 15)]
    || ' ' ||
    (
        ARRAY[
            'Adams','Baker','Carter','Davis','Evans',
            'Foster','Green','Harris','Irwin','Jackson',
            'King','Long','Moore','Nelson','Owens'
        ]
    )[1 + ((gs - 1) % 15)],

    'contact' || gs || '@customer.example',

    (
        ARRAY[
            'VP Engineering',
            'Director Operations',
            'CFO',
            'CTO',
            'Procurement Manager',
            'Program Director',
            'IT Director',
            'Product Director'
        ]
    )[1 + ((gs - 1) % 8)],

    (
        ARRAY[
            'Engineering',
            'Operations',
            'Finance',
            'IT',
            'Procurement',
            'Product'
        ]
    )[1 + ((gs - 1) % 6)],

    CASE
        WHEN gs % 3 = 0 THEN 'Executive'
        WHEN gs % 2 = 0 THEN 'Senior'
        ELSE 'Mid'
    END,

    CASE
        WHEN gs % 7 = 0 THEN 'Executive Sponsor'
        WHEN gs % 5 = 0 THEN 'Decision Maker'
        WHEN gs % 3 = 0 THEN 'Project Stakeholder'
        ELSE 'Technical Contact'
    END,

    gs % 5 = 0
FROM generate_series(1, 500) gs;


-- ============================================================
-- VENDORS
-- ============================================================

INSERT INTO vendors (
    vendor_id,
    vendor_code,
    vendor_name,
    vendor_category,
    region,
    risk_level,
    annual_spend
)
SELECT
    'V' || LPAD(gs::TEXT, 4, '0'),
    'VEND-' || LPAD(gs::TEXT, 4, '0'),

    (
        ARRAY[
            'CloudSphere',
            'DataForge',
            'SecureNet',
            'GlobalSoft',
            'TechSource',
            'InfraWorks',
            'Prime Consulting',
            'DigitalOps',
            'Apex Systems',
            'NorthStar Services'
        ]
    )[1 + ((gs - 1) % 10)]
    || ' ' || gs,

    (
        ARRAY[
            'Cloud Infrastructure',
            'Software',
            'Security',
            'Consulting',
            'Hardware',
            'Managed Services',
            'Data',
            'Networking'
        ]
    )[1 + ((gs - 1) % 8)],

    (
        ARRAY[
            'North America',
            'Europe',
            'Asia Pacific',
            'India'
        ]
    )[1 + ((gs - 1) % 4)],

    CASE
        WHEN gs % 37 = 0 THEN 'Critical'
        WHEN gs % 11 = 0 THEN 'High'
        WHEN gs % 4 = 0 THEN 'Medium'
        ELSE 'Low'
    END,

    ROUND(
        (50000 + random() * 5000000)::NUMERIC,
        2
    )
FROM generate_series(1, 150) gs;


-- ============================================================
-- PROJECTS
-- ============================================================

INSERT INTO projects (
    project_id,
    project_code,
    customer_id,
    project_name,
    project_type,
    description,
    project_status,
    health_status,
    priority,
    project_manager_id,
    technical_lead_id,
    account_manager_id,
    start_date,
    planned_end_date,
    budget,
    actual_spend,
    completion_percent
)
SELECT
    'P' || LPAD(gs::TEXT, 5, '0'),
    'PROJ-' || LPAD(gs::TEXT, 5, '0'),

    'C' || LPAD(
        (((gs - 1) % 100) + 1)::TEXT,
        4,
        '0'
    ),

    (
        ARRAY[
            'Phoenix',
            'Atlas',
            'Medusa',
            'Gotham',
            'Umbra',
            'Apollo',
            'Orion',
            'Mercury',
            'Titan',
            'Helios',
            'Nova',
            'Vertex',
            'Horizon',
            'Summit',
            'Aurora'
        ]
    )[1 + ((gs - 1) % 15)]
    || ' '
    || CEIL(gs / 15.0)::INT,

    (
        ARRAY[
            'Digital Transformation',
            'Cloud Migration',
            'Data Platform',
            'AI Platform',
            'ERP Modernization',
            'Application Development',
            'Cybersecurity',
            'Infrastructure',
            'Analytics',
            'Customer Experience'
        ]
    )[1 + ((gs - 1) % 10)],

    'Enterprise initiative covering '
    ||
    (
        ARRAY[
            'platform modernization',
            'application modernization',
            'data transformation',
            'cloud migration',
            'AI adoption',
            'security modernization',
            'process automation'
        ]
    )[1 + ((gs - 1) % 7)],

    CASE
        WHEN gs % 20 = 0 THEN 'On Hold'
        WHEN gs % 37 = 0 THEN 'Completed'
        WHEN gs % 47 = 0 THEN 'Planned'
        ELSE 'Active'
    END,

    CASE
        WHEN gs % 29 = 0 THEN 'Critical'
        WHEN gs % 7 = 0 THEN 'At Risk'
        WHEN gs % 11 = 0 THEN 'Delayed'
        ELSE 'On Track'
    END,

    CASE
        WHEN gs % 25 = 0 THEN 'Critical'
        WHEN gs % 7 = 0 THEN 'High'
        WHEN gs % 3 = 0 THEN 'Medium'
        ELSE 'Low'
    END,

    'E' || LPAD(
        (1 + ((gs * 7) % 250))::TEXT,
        4,
        '0'
    ),

    'E' || LPAD(
        (1 + ((gs * 11) % 250))::TEXT,
        4,
        '0'
    ),

    'E' || LPAD(
        (1 + ((gs * 13) % 250))::TEXT,
        4,
        '0'
    ),

    DATE '2025-01-01' + ((gs * 3) % 650),

    DATE '2026-04-01' + ((gs * 7) % 500),

    ROUND(
        (100000 + random() * 2900000)::NUMERIC,
        2
    ),

    ROUND(
        (50000 + random() * 2000000)::NUMERIC,
        2
    ),

    CASE
        WHEN gs % 37 = 0 THEN 100
        WHEN gs % 7 = 0 THEN 35 + random() * 45
        ELSE 50 + random() * 45
    END
FROM generate_series(1, 300) gs;


-- ============================================================
-- PROJECT MEMBERS
-- ============================================================

INSERT INTO project_members (
    project_id,
    employee_id,
    role,
    allocation_percent,
    joined_date
)
SELECT DISTINCT
    p.project_id,
    'E' || LPAD(
        (
            1 +
            ((p_num * multiplier) % 250)
        )::TEXT,
        4,
        '0'
    ),

    CASE multiplier
        WHEN 1 THEN 'Project Manager'
        WHEN 2 THEN 'Technical Lead'
        WHEN 3 THEN 'Software Engineer'
        WHEN 4 THEN 'Business Analyst'
        WHEN 5 THEN 'QA Engineer'
        WHEN 6 THEN 'Solutions Architect'
        ELSE 'Engineer'
    END,

    CASE
        WHEN multiplier <= 2 THEN 75
        WHEN multiplier <= 4 THEN 50
        ELSE 25
    END,

    p.start_date
FROM (
    SELECT
        project_id,
        start_date,
        substring(project_id from 2)::INT AS p_num
    FROM projects
) p
CROSS JOIN generate_series(1, 7) multiplier;


-- ============================================================
-- CONTRACTS
-- ============================================================

INSERT INTO contracts (
    contract_id,
    contract_number,
    customer_id,
    vendor_id,
    project_id,
    contract_type,
    contract_status,
    start_date,
    end_date,
    contract_value,
    renewal_type,
    owner_employee_id
)
SELECT
    'CON' || LPAD(gs::TEXT, 5, '0'),
    'CTR-' || LPAD(gs::TEXT, 6, '0'),

    CASE
        WHEN gs % 4 <> 0 THEN
            'C' || LPAD(
                (((gs - 1) % 100) + 1)::TEXT,
                4,
                '0'
            )
        ELSE NULL
    END,

    CASE
        WHEN gs % 4 = 0 THEN
            'V' || LPAD(
                (((gs - 1) % 150) + 1)::TEXT,
                4,
                '0'
            )
        ELSE NULL
    END,

    CASE
        WHEN gs % 5 <> 0 THEN
            'P' || LPAD(
                (((gs - 1) % 300) + 1)::TEXT,
                5,
                '0'
            )
        ELSE NULL
    END,

    (
        ARRAY[
            'Master Services Agreement',
            'Statement of Work',
            'Software License',
            'Consulting Agreement',
            'Support Agreement',
            'Vendor Agreement'
        ]
    )[1 + ((gs - 1) % 6)],

    CASE
        WHEN gs % 31 = 0 THEN 'Expired'
        WHEN gs % 17 = 0 THEN 'Under Review'
        ELSE 'Active'
    END,

    DATE '2025-01-01' + ((gs * 5) % 500),

    DATE '2026-01-01' + ((gs * 7) % 900),

    ROUND(
        (50000 + random() * 3000000)::NUMERIC,
        2
    ),

    CASE
        WHEN gs % 3 = 0 THEN 'Auto Renew'
        WHEN gs % 3 = 1 THEN 'Manual'
        ELSE 'None'
    END,

    'E' || LPAD(
        (1 + ((gs * 17) % 250))::TEXT,
        4,
        '0'
    )
FROM generate_series(1, 300) gs;


-- ============================================================
-- INVOICES
-- ============================================================

INSERT INTO invoices (
    invoice_id,
    invoice_number,
    customer_id,
    project_id,
    invoice_date,
    due_date,
    amount,
    status,
    payment_date,
    payment_method,
    description
)
SELECT
    'INV' || LPAD(gs::TEXT, 6, '0'),
    'INV-' || LPAD(gs::TEXT, 8, '0'),

    p.customer_id,
    p.project_id,

    DATE '2026-01-01'
        + ((gs * 3) % 300),

    DATE '2026-02-01'
        + ((gs * 5) % 300),

    ROUND(
        (10000 + random() * 250000)::NUMERIC,
        2
    ),

    CASE
        WHEN gs % 23 = 0 THEN 'Disputed'
        WHEN gs % 19 = 0 THEN 'Cancelled'
        WHEN gs % 7 = 0 THEN 'Overdue'
        WHEN gs % 5 = 0 THEN 'Partially Paid'
        WHEN gs % 3 = 0 THEN 'Paid'
        ELSE 'Pending'
    END,

    CASE
        WHEN gs % 3 = 0 THEN
            DATE '2026-03-01'
            + ((gs * 2) % 250)
        ELSE NULL
    END,

    CASE
        WHEN gs % 3 = 0 THEN
            (
                ARRAY[
                    'ACH',
                    'Wire Transfer',
                    'Credit Card',
                    'Check'
                ]
            )[1 + ((gs - 1) % 4)]
        ELSE NULL
    END,

    (
        ARRAY[
            'Monthly project billing',
            'Milestone payment',
            'Professional services',
            'Cloud infrastructure',
            'Implementation services',
            'Support and maintenance',
            'Change request'
        ]
    )[1 + ((gs - 1) % 7)]

FROM generate_series(1, 1600) gs

JOIN projects p
    ON p.project_id =
       'P' || LPAD(
           (((gs - 1) % 300) + 1)::TEXT,
           5,
           '0'
       );


-- ============================================================
-- TICKETS
-- ============================================================

INSERT INTO tickets (
    ticket_id,
    ticket_number,
    project_id,
    customer_id,
    title,
    description,
    category,
    severity,
    status,
    priority,
    assigned_to,
    reported_by_contact,
    created_at,
    resolved_at,
    sla_due_at,
    root_cause
)
SELECT
    'T' || LPAD(gs::TEXT, 7, '0'),
    'TKT-' || LPAD(gs::TEXT, 8, '0'),

    p.project_id,
    p.customer_id,

    (
        ARRAY[
            'Payment integration failing',
            'Authentication service timeout',
            'Data migration validation issue',
            'Customer approval pending',
            'API response latency',
            'Production deployment failure',
            'Dashboard formatting issue',
            'Database connection failure',
            'Incorrect report totals',
            'File upload failure',
            'User provisioning issue',
            'Third-party API unavailable',
            'Security policy violation',
            'Performance degradation',
            'Workflow configuration issue'
        ]
    )[1 + ((gs - 1) % 15)],

    'Issue reported during '
    ||
    (
        ARRAY[
            'integration testing',
            'user acceptance testing',
            'production deployment',
            'data migration',
            'weekly operations',
            'security validation'
        ]
    )[1 + ((gs - 1) % 6)],

    (
        ARRAY[
            'Integration',
            'Infrastructure',
            'Application',
            'Data',
            'Security',
            'Performance',
            'Access',
            'Reporting'
        ]
    )[1 + ((gs - 1) % 8)],

    CASE
        WHEN gs % 31 = 0 THEN 'Critical'
        WHEN gs % 9 = 0 THEN 'High'
        WHEN gs % 3 = 0 THEN 'Medium'
        ELSE 'Low'
    END,

    CASE
        WHEN gs % 17 = 0 THEN 'Blocked'
        WHEN gs % 11 = 0 THEN 'Resolved'
        WHEN gs % 7 = 0 THEN 'Closed'
        WHEN gs % 3 = 0 THEN 'In Progress'
        ELSE 'Open'
    END,

    CASE
        WHEN gs % 31 = 0 THEN 'Critical'
        WHEN gs % 9 = 0 THEN 'High'
        WHEN gs % 3 = 0 THEN 'Medium'
        ELSE 'Low'
    END,

    p.project_manager_id,

    'CT' || LPAD(
        (1 + ((gs * 7) % 500))::TEXT,
        5,
        '0'
    ),

    TIMESTAMPTZ '2026-01-01'
        + ((gs * 17) % 280) * INTERVAL '1 day',

    CASE
        WHEN gs % 11 = 0 THEN
            TIMESTAMPTZ '2026-02-01'
            + ((gs * 17) % 280) * INTERVAL '1 day'
        ELSE NULL
    END,

    TIMESTAMPTZ '2026-01-01'
        + ((gs * 17) % 280) * INTERVAL '1 day'
        + INTERVAL '3 days',

    CASE
        WHEN gs % 31 = 0 THEN
            'Third-party dependency failure'
        WHEN gs % 17 = 0 THEN
            'Customer approval or dependency blocked'
        WHEN gs % 13 = 0 THEN
            'Configuration defect'
        ELSE
            'Under investigation'
    END

FROM generate_series(1, 3200) gs

JOIN projects p
    ON p.project_id =
       'P' || LPAD(
           (((gs - 1) % 300) + 1)::TEXT,
           5,
           '0'
       );


-- ============================================================
-- DOCUMENTS
-- ============================================================

INSERT INTO documents (
    document_id,
    document_number,
    project_id,
    customer_id,
    document_type,
    title,
    summary,
    document_status,
    author_employee_id,
    created_at,
    updated_at,
    content
)
SELECT
    'DOC' || LPAD(gs::TEXT, 6, '0'),
    'DOC-' || LPAD(gs::TEXT, 8, '0'),

    p.project_id,
    p.customer_id,

    (
        ARRAY[
            'Meeting Notes',
            'Project Plan',
            'Architecture Document',
            'Status Report',
            'Incident Report',
            'Requirements',
            'Risk Register',
            'Decision Log',
            'Technical Specification',
            'Change Request'
        ]
    )[1 + ((gs - 1) % 10)],

    (
        ARRAY[
            'Weekly Project Steering Committee',
            'Delivery Plan',
            'Architecture Review',
            'Monthly Status Report',
            'Production Incident',
            'Business Requirements',
            'Project Risk Register',
            'Architecture Decision Record',
            'Technical Design',
            'Change Request Review'
        ]
    )[1 + ((gs - 1) % 10)],

    'Enterprise project documentation for '
    || p.project_name,

    CASE
        WHEN gs % 19 = 0 THEN 'Under Review'
        WHEN gs % 11 = 0 THEN 'Draft'
        WHEN gs % 13 = 0 THEN 'Archived'
        ELSE 'Final'
    END,

    p.project_manager_id,

    TIMESTAMPTZ '2026-01-01'
        + ((gs * 13) % 280) * INTERVAL '1 day',

    TIMESTAMPTZ '2026-01-01'
        + ((gs * 13) % 280) * INTERVAL '1 day'
        + INTERVAL '2 days',

    'Project '
    || p.project_name
    || ' documentation. '
    || CASE
        WHEN p.health_status = 'At Risk'
            THEN 'Current risks include delivery dependencies, unresolved issues, and financial exposure.'
        WHEN p.health_status = 'Delayed'
            THEN 'The project has experienced schedule delays and requires active stakeholder management.'
        WHEN p.health_status = 'Critical'
            THEN 'Immediate executive attention is required due to significant delivery risk.'
        ELSE
            'The project is progressing according to the current delivery plan.'
       END
    || ' Additional context should be validated against project tickets, invoices, meetings and activities.'

FROM generate_series(1, 1100) gs

JOIN projects p
    ON p.project_id =
       'P' || LPAD(
           (((gs - 1) % 300) + 1)::TEXT,
           5,
           '0'
       );


-- ============================================================
-- MEETINGS
-- ============================================================

INSERT INTO meetings (
    meeting_id,
    project_id,
    customer_id,
    meeting_type,
    title,
    scheduled_at,
    duration_minutes,
    organizer_id,
    summary,
    decisions,
    action_items,
    next_meeting_date
)
SELECT
    'M' || LPAD(gs::TEXT, 6, '0'),

    p.project_id,
    p.customer_id,

    (
        ARRAY[
            'Weekly Status',
            'Steering Committee',
            'Technical Review',
            'Customer Review',
            'Incident Review',
            'Sprint Planning',
            'Executive Review',
            'Architecture Review'
        ]
    )[1 + ((gs - 1) % 8)],

    p.project_name || ' - ' ||
    (
        ARRAY[
            'Weekly Status',
            'Steering Committee',
            'Technical Review',
            'Customer Review',
            'Incident Review'
        ]
    )[1 + ((gs - 1) % 5)],

    TIMESTAMPTZ '2026-01-01'
        + ((gs * 7) % 280) * INTERVAL '1 day',

    (
        ARRAY[
            30,
            45,
            60,
            90,
            120
        ]
    )[1 + ((gs - 1) % 5)],

    p.project_manager_id,

    CASE
        WHEN p.health_status IN ('At Risk', 'Critical') THEN
            'The team reviewed active delivery risks, unresolved dependencies and stakeholder concerns.'
        WHEN p.health_status = 'Delayed' THEN
            'The team reviewed schedule variance and recovery actions.'
        ELSE
            'The team reviewed delivery progress, upcoming milestones and open actions.'
    END,

    CASE
        WHEN p.health_status IN ('At Risk', 'Critical') THEN
            'Escalate unresolved dependencies and review mitigation plan.'
        ELSE
            'Continue execution against the current delivery plan.'
    END,

    CASE
        WHEN p.health_status IN ('At Risk', 'Critical') THEN
            'Project manager to provide updated risk assessment and action plan.'
        ELSE
            'Team members to complete assigned actions before next review.'
    END,

    DATE '2026-10-01' + ((gs * 3) % 90)

FROM generate_series(1, 1600) gs

JOIN projects p
    ON p.project_id =
       'P' || LPAD(
           (((gs - 1) % 300) + 1)::TEXT,
           5,
           '0'
       );


-- ============================================================
-- ACTIVITIES
-- ============================================================

INSERT INTO activities (
    customer_id,
    project_id,
    employee_id,
    activity_type,
    subject,
    description,
    activity_status,
    occurred_at
)
SELECT
    p.customer_id,
    p.project_id,

    CASE
        WHEN gs % 3 = 0 THEN p.project_manager_id
        WHEN gs % 3 = 1 THEN p.technical_lead_id
        ELSE p.account_manager_id
    END,

    (
        ARRAY[
            'Email',
            'Call',
            'Status Update',
            'Escalation',
            'Customer Interaction',
            'Internal Note',
            'Approval',
            'Risk Update',
            'Financial Update',
            'Technical Update'
        ]
    )[1 + ((gs - 1) % 10)],

    (
        ARRAY[
            'Customer status discussion',
            'Project delivery update',
            'Risk escalation',
            'Invoice follow-up',
            'Technical dependency discussion',
            'Approval request',
            'Project milestone update',
            'Stakeholder communication',
            'Issue escalation',
            'Weekly account review'
        ]
    )[1 + ((gs - 1) % 10)],

    CASE
        WHEN p.health_status IN ('At Risk', 'Critical') THEN
            'Activity related to active project risk, stakeholder communication or remediation.'
        ELSE
            'Routine project and customer activity.'
    END,

    CASE
        WHEN gs % 11 = 0 THEN 'Escalated'
        WHEN gs % 7 = 0 THEN 'Pending'
        ELSE 'Completed'
    END,

    TIMESTAMPTZ '2026-01-01'
        + ((gs * 11) % 280) * INTERVAL '1 day'

FROM generate_series(1, 5200) gs

JOIN projects p
    ON p.project_id =
       'P' || LPAD(
           (((gs - 1) % 300) + 1)::TEXT,
           5,
           '0'
       );


-- ============================================================
-- INTENTIONAL "INTERESTING" DATA
-- ============================================================
--
-- These records are important.
-- They create scenarios where an agent needs to combine
-- multiple sources instead of simply filtering one table.
-- ============================================================


-- ------------------------------------------------------------
-- Phoenix-like critical projects
-- ------------------------------------------------------------

UPDATE projects
SET
    health_status = 'At Risk',
    priority = 'High'
WHERE project_id IN ('P00001', 'P00002', 'P00003', 'P00004', 'P00005');


-- ------------------------------------------------------------
-- Force overdue invoices on those projects
-- ------------------------------------------------------------

UPDATE invoices
SET
    status = 'Overdue',
    due_date = DATE '2026-08-30'
WHERE project_id IN (
    'P00001',
    'P00002',
    'P00003',
    'P00004',
    'P00005'
)
AND invoice_id IN (
    SELECT invoice_id
    FROM invoices
    WHERE project_id IN (
        'P00001',
        'P00002',
        'P00003',
        'P00004',
        'P00005'
    )
    LIMIT 10
);


-- ------------------------------------------------------------
-- Critical tickets
-- ------------------------------------------------------------

UPDATE tickets
SET
    severity = 'Critical',
    priority = 'Critical',
    status = 'Open'
WHERE project_id IN (
    'P00001',
    'P00002',
    'P00003',
    'P00004',
    'P00005'
)
AND ticket_id IN (
    SELECT ticket_id
    FROM tickets
    WHERE project_id IN (
        'P00001',
        'P00002',
        'P00003',
        'P00004',
        'P00005'
    )
    LIMIT 15
);


-- ------------------------------------------------------------
-- Blocked customer approvals
-- ------------------------------------------------------------

UPDATE tickets
SET
    title = 'Customer approval pending',
    category = 'Integration',
    severity = 'High',
    priority = 'High',
    status = 'Blocked',
    root_cause = 'Customer approval pending'
WHERE ticket_id IN (
    SELECT ticket_id
    FROM tickets
    WHERE project_id = 'P00001'
    LIMIT 2
);


-- ------------------------------------------------------------
-- Force one project to have strong financial exposure
-- ------------------------------------------------------------

UPDATE projects
SET
    project_name = 'Phoenix Enterprise Transformation',
    description =
        'Large enterprise transformation involving payment integration, customer approvals and financial reconciliation.',
    budget = 450000,
    actual_spend = 390000,
    completion_percent = 61
WHERE project_id = 'P00001';


-- ------------------------------------------------------------
-- Documents with richer context
-- ------------------------------------------------------------

INSERT INTO documents (
    document_id,
    document_number,
    project_id,
    customer_id,
    document_type,
    title,
    summary,
    document_status,
    author_employee_id,
    created_at,
    updated_at,
    content
)
SELECT
    'DOC-PHOENIX-001',
    'DOC-PHX-001',
    'P00001',
    p.customer_id,
    'Meeting Notes',
    'Phoenix Weekly Steering Committee',
    'Customer approval for payment workflow is pending. Integration team expects approximately 10 business days.',
    'Final',
    p.project_manager_id,
    NOW() - INTERVAL '12 days',
    NOW() - INTERVAL '10 days',
    'Phoenix steering committee notes: payment integration remains on the critical path. Customer approval for the payment workflow is still pending. The integration team estimates approximately 10 business days after approval. Finance also flagged an overdue invoice that should be reviewed with the account team.'
FROM projects p
WHERE p.project_id = 'P00001';


INSERT INTO documents (
    document_id,
    document_number,
    project_id,
    customer_id,
    document_type,
    title,
    summary,
    document_status,
    author_employee_id,
    created_at,
    updated_at,
    content
)
SELECT
    'DOC-PHOENIX-002',
    'DOC-PHX-002',
    'P00001',
    p.customer_id,
    'Project Plan',
    'Phoenix Delivery Plan',
    'Payment integration is on the critical path.',
    'Final',
    p.project_manager_id,
    NOW() - INTERVAL '30 days',
    NOW() - INTERVAL '25 days',
    'Phoenix delivery plan. Payment integration is on the critical path. Any delay in customer approval will affect downstream testing and deployment activities. Project management should monitor approval status, critical tickets and financial exposure.'
FROM projects p
WHERE p.project_id = 'P00001';


-- ============================================================
-- ADDITIONAL SPECIAL CASES
-- ============================================================

-- A project with an overdue invoice but otherwise healthy.
UPDATE projects
SET health_status = 'On Track'
WHERE project_id = 'P00025';

UPDATE invoices
SET
    status = 'Overdue',
    due_date = DATE '2026-08-01'
WHERE invoice_id = (
    SELECT invoice_id
    FROM invoices
    WHERE project_id = 'P00025'
    LIMIT 1
);


-- A project with critical tickets but no overdue invoice.
UPDATE projects
SET health_status = 'At Risk'
WHERE project_id = 'P00040';

UPDATE tickets
SET
    severity = 'Critical',
    priority = 'Critical',
    status = 'Open'
WHERE ticket_id IN (
    SELECT ticket_id
    FROM tickets
    WHERE project_id = 'P00040'
    LIMIT 3
);


-- A delayed project caused primarily by external approval.
UPDATE projects
SET
    health_status = 'Delayed',
    description =
        'Project delayed due to regulatory and customer approval dependencies.'
WHERE project_id = 'P00055';

UPDATE tickets
SET
    title = 'Regulatory validation pending',
    severity = 'Critical',
    priority = 'High',
    status = 'Blocked',
    root_cause = 'External regulatory approval'
WHERE ticket_id IN (
    SELECT ticket_id
    FROM tickets
    WHERE project_id = 'P00055'
    LIMIT 1
);


-- ============================================================
-- UPDATE CUSTOMER HEALTH
-- ============================================================

UPDATE customers c
SET account_status = 'At Risk'
WHERE c.customer_id IN (
    SELECT customer_id
    FROM projects
    WHERE health_status IN ('At Risk', 'Critical', 'Delayed')
    GROUP BY customer_id
    HAVING COUNT(*) >= 2
);


-- ============================================================
-- DATA VALIDATION
-- ============================================================

SELECT 'customers' AS table_name, COUNT(*) AS row_count
FROM customers

UNION ALL

SELECT 'employees', COUNT(*)
FROM employees

UNION ALL

SELECT 'contacts', COUNT(*)
FROM contacts

UNION ALL

SELECT 'vendors', COUNT(*)
FROM vendors

UNION ALL

SELECT 'projects', COUNT(*)
FROM projects

UNION ALL

SELECT 'project_members', COUNT(*)
FROM project_members

UNION ALL

SELECT 'contracts', COUNT(*)
FROM contracts

UNION ALL

SELECT 'invoices', COUNT(*)
FROM invoices

UNION ALL

SELECT 'tickets', COUNT(*)
FROM tickets

UNION ALL

SELECT 'documents', COUNT(*)
FROM documents

UNION ALL

SELECT 'meetings', COUNT(*)
FROM meetings

UNION ALL

SELECT 'activities', COUNT(*)
FROM activities

ORDER BY table_name;


-- ============================================================
-- BUSINESS HEALTH CHECK
-- ============================================================

SELECT
    COUNT(*) AS total_projects,

    COUNT(*) FILTER (
        WHERE health_status = 'On Track'
    ) AS on_track,

    COUNT(*) FILTER (
        WHERE health_status = 'At Risk'
    ) AS at_risk,

    COUNT(*) FILTER (
        WHERE health_status = 'Delayed'
    ) AS delayed,

    COUNT(*) FILTER (
        WHERE health_status = 'Critical'
    ) AS critical

FROM projects;


SELECT
    COUNT(*) AS total_invoices,

    COUNT(*) FILTER (
        WHERE status = 'Paid'
    ) AS paid,

    COUNT(*) FILTER (
        WHERE status = 'Pending'
    ) AS pending,

    COUNT(*) FILTER (
        WHERE status = 'Overdue'
    ) AS overdue,

    COALESCE(
        SUM(amount) FILTER (
            WHERE status = 'Overdue'
        ),
        0
    ) AS overdue_amount

FROM invoices;


SELECT
    COUNT(*) AS total_tickets,

    COUNT(*) FILTER (
        WHERE severity = 'Critical'
        AND status NOT IN ('Resolved', 'Closed')
    ) AS open_critical,

    COUNT(*) FILTER (
        WHERE status = 'Blocked'
    ) AS blocked

FROM tickets;


-- ============================================================
-- SAMPLE AGENT QUERIES
-- ============================================================

-- Which projects belong to Acme-like customer?
SELECT
    p.project_id,
    p.project_name,
    c.company_name,
    p.health_status,
    p.budget
FROM projects p
JOIN customers c
    ON c.customer_id = p.customer_id
WHERE c.company_name ILIKE 'Acme%';


-- Projects with overdue invoices
SELECT *
FROM v_project_health
WHERE overdue_invoice_count > 0
ORDER BY overdue_invoice_amount DESC;


-- Customers with both risky projects AND overdue invoices
SELECT *
FROM v_customer_health
WHERE risky_project_count > 0
  AND overdue_invoice_count > 0
ORDER BY overdue_invoice_amount DESC;


-- Projects requiring immediate attention
SELECT *
FROM v_project_health
WHERE critical_ticket_count >= 2
   OR overdue_invoice_count >= 1
   OR blocked_ticket_count >= 2
ORDER BY
    critical_ticket_count DESC,
    overdue_invoice_amount DESC;


-- ============================================================
-- DONE
-- ============================================================

SELECT 'NexusWorks synthetic enterprise data seeded successfully.' AS message;