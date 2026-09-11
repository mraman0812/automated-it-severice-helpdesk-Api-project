def test_analytics_tickets(client, agent_token):
    response = client.get(
        "/api/v1/analytics/tickets",
        headers={"Authorization": f"Bearer {agent_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "total" in data
    assert "open" in data
    assert "resolved" in data


def test_analytics_categories(client, agent_token):
    response = client.get(
        "/api/v1/analytics/categories",
        headers={"Authorization": f"Bearer {agent_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "distribution" in data


def test_analytics_sla(client, admin_token):
    response = client.get(
        "/api/v1/analytics/sla",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "sla_compliance" in data
    assert "average_resolution_time_hours" in data
