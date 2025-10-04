def test_update_progress(client):
    # create course
    course_resp = client.post("/courses/", json={"name": "Finance"})
    course_id = course_resp.json()["id"]

    # update progress
    response = client.post("/progress/update", json={
        "course_id": course_id,
        "num_topics_mastered": 2,
        "num_quizzes_taken": 1
    })
    assert response.status_code == 200
    progress = response.json()
    assert progress["num_topics_mastered"] == 2
    assert progress["num_quizzes_taken"] == 1
