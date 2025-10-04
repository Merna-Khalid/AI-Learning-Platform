def test_generate_quiz_with_topics(client, db_session):
    # create a course
    course_resp = client.post("/courses/", json={"name": "Japanese"})
    course_id = course_resp.json()["id"]

    # create topics
    t1 = client.post(f"/topics/", json={"course_id": course_id, "name": "Hiragana"}).json()
    t2 = client.post(f"/topics/", json={"course_id": course_id, "name": "Katakana"}).json()

    # generate quiz
    response = client.post("/quizzes/generate", json={
        "course_id": course_id,
        "topic_ids": [t1["id"], t2["id"]],
        "num_questions": 3
    })

    assert response.status_code == 200
    quiz = response.json()
    assert quiz["course_id"] == course_id
    assert len(quiz["questions"]) == 3
