from typing import Any

from app.tools.base import Tool


DATABASE_SCHEMA = """
NexusWorks Enterprise Database

TABLE: customers
- customer_id
- company_name
- industry
- account_status
- account_manager_id
- created_at

TABLE: employees
- employee_id
- first_name
- last_name
- email
- department
- job_title
- manager_id
- employment_status

TABLE: contacts
- contact_id
- customer_id
- first_name
- last_name
- email
- phone
- job_title

TABLE: vendors
- vendor_id
- vendor_name
- category
- status

TABLE: projects
- project_id
- customer_id
- project_name
- description
- status
- priority
- start_date
- target_end_date
- budget
- actual_spend
- completion_percent
- health_status

TABLE: project_members
- project_id
- employee_id
- role
- allocation_percent

TABLE: contracts
- contract_id
- customer_id
- project_id
- contract_name
- contract_value
- start_date
- end_date
- status

TABLE: invoices
- invoice_id
- customer_id
- project_id
- invoice_number
- invoice_date
- due_date
- amount
- status
- paid_date

TABLE: tickets
- ticket_id
- customer_id
- project_id
- title
- description
- priority
- status
- created_at
- resolved_at

TABLE: documents
- document_id
- customer_id
- project_id
- title
- document_type
- content
- created_at

TABLE: meetings
- meeting_id
- customer_id
- project_id
- title
- meeting_date
- notes

TABLE: activities
- activity_id
- customer_id
- project_id
- employee_id
- activity_type
- description
- activity_date

Important relationships:

customers.customer_id
    -> projects.customer_id

customers.customer_id
    -> contacts.customer_id

customers.customer_id
    -> contracts.customer_id

customers.customer_id
    -> invoices.customer_id

customers.customer_id
    -> tickets.customer_id

projects.project_id
    -> project_members.project_id

projects.project_id
    -> contracts.project_id

projects.project_id
    -> invoices.project_id

projects.project_id
    -> tickets.project_id

projects.project_id
    -> documents.project_id

projects.project_id
    -> meetings.project_id

projects.project_id
    -> activities.project_id

employees.employee_id
    -> project_members.employee_id
"""


class SchemaTool(Tool):

    @property
    def name(self) -> str:
        return "get_schema"

    @property
    def description(self) -> str:
        return (
            "Returns the NexusWorks database schema, "
            "including tables, columns and relationships."
        )

    async def execute(self, arguments: dict[str, Any]) -> str:
        return DATABASE_SCHEMA