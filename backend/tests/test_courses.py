def test_create_course(client):
    response = client.post("/courses/", json={"name": "Deep Learning"})
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Deep Learning"
    assert "id" in data


def test_get_courses(client):
    # Add a course first
    client.post("/courses/", json={"name": "Finance"})
    response = client.get("/courses/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
