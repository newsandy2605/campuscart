def test_registration_accepts_gmail_and_email_otp(client):
    response = client.post("/api/auth/register", json={
        "name": "Gmail Student",
        "email": "student@gmail.com",
        "password": "StrongPass123!",
        "verification_channel": "email",
    })
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["verification_channel"] == "email"
    assert body["user"]["email"] == "student@gmail.com"
    assert body["otp_delivery"]["provider"] == "development"
    code = body["otp_delivery"]["debug_code"]

    verify = client.post("/api/auth/otp/verify", json={
        "channel": "email",
        "destination": "student@gmail.com",
        "purpose": "email_verification",
        "code": code,
    })
    assert verify.status_code == 200, verify.text
    assert verify.json()["user"]["email_verified"] is True


def test_indian_phone_normalization(client):
    response = client.post("/api/auth/register", json={
        "name": "Phone Student",
        "phone": "09876543210",
        "password": "StrongPass123!",
        "verification_channel": "phone",
    })
    assert response.status_code == 200, response.text
    assert response.json()["user"]["phone"] == "+919876543210"
    assert response.json()["verification_channel"] == "phone"


def test_verified_contact_can_self_select_campus(client, db):
    from app.models import Campus

    campus = Campus(
        name="Open Test University",
        slug="open-test-university",
        city="Pune",
        state="Maharashtra",
        pincode="411001",
        email_domain="",
    )
    db.add(campus)
    db.commit()

    response = client.post("/api/auth/register", json={
        "name": "Campus Student",
        "email": "campus.student@gmail.com",
        "password": "StrongPass123!",
        "verification_channel": "email",
    })
    assert response.status_code == 200, response.text
    body = response.json()
    verify = client.post("/api/auth/otp/verify", json={
        "channel": "email",
        "destination": "campus.student@gmail.com",
        "purpose": "email_verification",
        "code": body["otp_delivery"]["debug_code"],
    })
    assert verify.status_code == 200, verify.text

    token = verify.json()["token"]
    joined = client.post(
        "/api/campuses/open-test-university/join",
        json={"student_id": ""},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert joined.status_code == 200, joined.text
    assert joined.json()["campus_slug"] == "open-test-university"
    assert joined.json()["verification_method"] == "contact_otp"
