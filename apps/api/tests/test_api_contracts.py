from app.schemas import CaseCreate, RegisterRequest


def test_case_create_schema_accepts_title():
    payload = CaseCreate(title="Board call authenticity review")
    assert payload.title.startswith("Board")


def test_register_schema_requires_enterprise_org_fields():
    payload = RegisterRequest(
        email="forensics@example.com",
        password="long-secure-password",
        full_name="Forensics Lead",
        organization_name="Example Trust Office",
    )
    assert payload.organization_name == "Example Trust Office"

