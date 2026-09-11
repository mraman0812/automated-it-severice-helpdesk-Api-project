from app.ml.preprocessing import clean_text, combine_ticket_text


def test_clean_text():
    raw = "My VPN is NOT working!!! Check http://example.com/test and 192.168.1.1 now."
    cleaned = clean_text(raw)
    assert "not" in cleaned
    assert "vpn" in cleaned
    assert "working" in cleaned
    assert "http" not in cleaned


def test_standalone_prediction(client):
    response = client.post(
        "/api/v1/classification/predict",
        json={
            "title": "Cannot connect to VPN tunnel",
            "description": "AnyConnect VPN client says connection timed out.",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["category"] == "Network"
    assert data["subcategory"] == "VPN"
    assert data["department"] == "Network Support"
    assert data["confidence"] > 0.5


def test_batch_prediction(client):
    response = client.post(
        "/api/v1/classification/batch",
        json={
            "tickets": [
                {
                    "title": "Forgot my Windows password",
                    "description": "Locked out of computer, need password reset.",
                },
                {
                    "title": "ThinkPad battery is swelling",
                    "description": "Battery chassis is bulging and pushing touchpad.",
                },
            ]
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["results"]) == 2
    assert data["results"][0]["category"] == "Account & Access"
    assert data["results"][1]["category"] == "Hardware"


def test_human_feedback(client, employee_token, agent_token):
    # 1. Create a ticket
    res_ticket = client.post(
        "/api/v1/tickets",
        json={
            "title": "Need urgent network assist",
            "description": "Having issues connecting to internal network resources.",
        },
        headers={"Authorization": f"Bearer {employee_token}"},
    )
    ticket_id = res_ticket.json()["id"]

    # 2. Submit feedback
    res_feedback = client.post(
        "/api/v1/feedback",
        json={
            "ticket_id": ticket_id,
            "correct_category": "Network",
            "correct_subcategory": "VPN",
            "correct_priority": "HIGH",
            "comments": "Verified by senior technician",
        },
        headers={"Authorization": f"Bearer {agent_token}"},
    )
    assert res_feedback.status_code == 201
    assert res_feedback.json()["correct_category"] == "Network"
