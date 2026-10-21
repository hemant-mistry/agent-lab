from app.services.supabase import supabase_service

result = (
    supabase_service.client
    .table("customers")
    .select("customer_id, company_name")
    .limit(5)
    .execute()
)

print(result.data)