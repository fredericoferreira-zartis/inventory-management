"""
Tests for POST /api/orders (restocking order creation).
"""


def test_create_order_returns_201(client):
    payload = {
        "customer": "Restocking System",
        "items": [{"sku": "WDG-001", "name": "Widget A", "quantity": 450, "unit_price": 25.00}],
        "warehouse": "San Francisco",
        "category": "Sensors",
        "expected_delivery": "2025-07-15T00:00:00"
    }
    response = client.post("/api/orders", json=payload)
    assert response.status_code == 201


def test_create_order_status_is_submitted(client):
    payload = {
        "customer": "Restocking System",
        "items": [{"sku": "WDG-001", "name": "Widget A", "quantity": 450, "unit_price": 25.00}],
        "warehouse": "San Francisco",
        "category": "Sensors",
        "expected_delivery": "2025-07-15T00:00:00"
    }
    response = client.post("/api/orders", json=payload)
    assert response.json()["status"] == "Submitted"


def test_create_order_generates_rst_order_number(client):
    payload = {
        "customer": "Restocking System",
        "items": [{"sku": "PCB-001", "name": "PCB Assembly", "quantity": 100, "unit_price": 24.99}],
        "warehouse": "Tokyo",
        "category": "Circuit Boards",
        "expected_delivery": "2025-07-20T00:00:00"
    }
    response = client.post("/api/orders", json=payload)
    assert response.json()["order_number"].startswith("RST-")


def test_create_order_calculates_total_value(client):
    payload = {
        "customer": "Restocking System",
        "items": [
            {"sku": "WDG-001", "name": "Widget A", "quantity": 10, "unit_price": 100.00},
            {"sku": "PCB-001", "name": "PCB Assembly", "quantity": 5, "unit_price": 50.00}
        ],
        "warehouse": "San Francisco",
        "category": None,
        "expected_delivery": "2025-07-15T00:00:00"
    }
    response = client.post("/api/orders", json=payload)
    # 10 * 100.00 + 5 * 50.00 = 1250.00
    assert response.json()["total_value"] == 1250.00


def test_create_order_preserves_expected_delivery(client):
    expected = "2025-08-01T00:00:00"
    payload = {
        "customer": "Restocking System",
        "items": [{"sku": "SNS-001", "name": "Sensor", "quantity": 50, "unit_price": 30.00}],
        "warehouse": "London",
        "category": "Sensors",
        "expected_delivery": expected
    }
    response = client.post("/api/orders", json=payload)
    assert response.json()["expected_delivery"] == expected


def test_submitted_order_appears_in_get_orders(client):
    payload = {
        "customer": "Restocking System",
        "items": [{"sku": "SNS-002", "name": "Sensor Module", "quantity": 200, "unit_price": 45.00}],
        "warehouse": "London",
        "category": "Sensors",
        "expected_delivery": "2025-07-30T00:00:00"
    }
    post_response = client.post("/api/orders", json=payload)
    assert post_response.status_code == 201
    order_number = post_response.json()["order_number"]

    get_response = client.get("/api/orders?status=Submitted")
    assert get_response.status_code == 200
    order_numbers = [o["order_number"] for o in get_response.json()]
    assert order_number in order_numbers


def test_create_order_missing_required_field_returns_422(client):
    # Missing required 'customer' and 'expected_delivery'
    payload = {
        "items": [{"sku": "WDG-001", "name": "Widget", "quantity": 10, "unit_price": 10.0}]
    }
    response = client.post("/api/orders", json=payload)
    assert response.status_code == 422
