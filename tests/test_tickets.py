def test_create_ticket_with_ml(client, employee_token):
    response = client.post(
        "/api/v1/tickets",
        json={
            "title": "Cannot connect to company VPN from home",
            "description": "Cisco AnyConnect connection fails every time I authenticate.",
        },
        headers={"Authorization": f"Bearer {employee_token}"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["ticket_number"].startswith("IT-")
    assert data["category_name"] == "Network" or data["classification"]["category"] == "Network"
    assert data["department_name"] == "Network Support"
    assert data["confidence_score"] > 0
    assert "id" in data


def test_list_tickets(client, employee_token):
    response = client.get(
        "/api/v1/tickets",
        headers={"Authorization": f"Bearer {employee_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data


def test_ticket_lifecycle(client, employee_token, agent_token):
    # 1. Create ticket
    res_create = client.post(
        "/api/v1/tickets",
        json={
            "title": "Network outage on third floor",
            "description": "Ethernet and WiFi access points have failed on 3rd floor.",
        },
        headers={"Authorization": f"Bearer {employee_token}"},
    )
    ticket_id = res_create.json()["id"]

    # 2. Resolve ticket as Agent
    res_resolve = client.post(
        f"/api/v1/tickets/{ticket_id}/resolve",
        json={"resolution": "Reset the switch port and restored power to access points."},
        headers={"Authorization": f"Bearer {agent_token}"},
    )
    assert res_resolve.status_code == 200
    assert res_resolve.json()["status"] == "RESOLVED"
    assert res_resolve.json()["resolution_note"] is not None

    # 3. Close ticket as User
    res_close = client.post(
        f"/api/v1/tickets/{ticket_id}/close",
        headers={"Authorization": f"Bearer {employee_token}"},
    )
    assert res_close.status_code == 200
    assert res_close.json()["status"] == "CLOSED"

    # 4. Reopen ticket as User
    res_reopen = client.post(
        f"/api/v1/tickets/{ticket_id}/reopen",
        headers={"Authorization": f"Bearer {employee_token}"},
    )
    assert res_reopen.status_code == 200
    assert res_reopen.json()["status"] == "REOPENED"
