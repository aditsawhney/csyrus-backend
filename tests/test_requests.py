from app.models.enums import Priority, UserRole


def test_requester_can_create_request(client, make_user, auth_headers):
    requester = make_user(UserRole.REQUESTER)
    reviewer = make_user(UserRole.REVIEWER)

    response = client.post(
        "/requests",
        headers=auth_headers(requester),
        json={
            "title": "Expense sign-off",
            "description": "Reimbursement for client dinner",
            "priority": Priority.HIGH.value,
            "reviewer_id": str(reviewer.id),
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "PENDING"
    assert body["reviewer_id"] == str(reviewer.id)


def test_create_request_rejects_unknown_reviewer(client, make_user, auth_headers):
    requester = make_user(UserRole.REQUESTER)

    response = client.post(
        "/requests",
        headers=auth_headers(requester),
        json={
            "title": "Bad reviewer",
            "description": "...",
            "priority": "LOW",
            "reviewer_id": "00000000-0000-0000-0000-000000000000",
        },
    )
    assert response.status_code == 404


def test_reviewer_cannot_create_request(client, make_user, auth_headers):
    reviewer = make_user(UserRole.REVIEWER)
    other_reviewer = make_user(UserRole.REVIEWER)

    response = client.post(
        "/requests",
        headers=auth_headers(reviewer),
        json={
            "title": "Should fail",
            "description": "Wrong role",
            "priority": Priority.LOW.value,
            "reviewer_id": str(other_reviewer.id),
        },
    )

    assert response.status_code == 403


def test_requester_can_list_only_their_requests(client, make_user, auth_headers):
    requester_a = make_user(UserRole.REQUESTER)
    requester_b = make_user(UserRole.REQUESTER)
    reviewer = make_user(UserRole.REVIEWER)

    client.post(
        "/requests",
        headers=auth_headers(requester_a),
        json={"title": "A's request", "description": "...", "priority": "LOW", "reviewer_id": str(reviewer.id)},
    )
    client.post(
        "/requests",
        headers=auth_headers(requester_b),
        json={"title": "B's request", "description": "...", "priority": "LOW", "reviewer_id": str(reviewer.id)},
    )

    response = client.get("/requests", headers=auth_headers(requester_a))
    assert response.status_code == 200
    titles = [item["title"] for item in response.json()]
    assert titles == ["A's request"]


def test_requester_cannot_access_others_request(client, make_user, auth_headers):
    requester_a = make_user(UserRole.REQUESTER)
    requester_b = make_user(UserRole.REQUESTER)
    reviewer = make_user(UserRole.REVIEWER)

    created = client.post(
        "/requests",
        headers=auth_headers(requester_a),
        json={"title": "Private", "description": "...", "priority": "LOW", "reviewer_id": str(reviewer.id)},
    ).json()

    response = client.get(f"/requests/{created['id']}", headers=auth_headers(requester_b))
    assert response.status_code == 403


def test_update_request_rejects_non_pending(client, make_user, auth_headers):
    requester = make_user(UserRole.REQUESTER)
    reviewer = make_user(UserRole.REVIEWER)

    created = client.post(
        "/requests",
        headers=auth_headers(requester),
        json={"title": "Edit me", "description": "...", "priority": "LOW", "reviewer_id": str(reviewer.id)},
    ).json()

    client.post(f"/reviewer/requests/{created['id']}/approve", headers=auth_headers(reviewer), json={"comments": "ok"})

    response = client.put(
        f"/requests/{created['id']}",
        headers=auth_headers(requester),
        json={"title": "New title"},
    )
    assert response.status_code == 409


def test_delete_pending_request(client, make_user, auth_headers):
    requester = make_user(UserRole.REQUESTER)
    reviewer = make_user(UserRole.REVIEWER)

    created = client.post(
        "/requests",
        headers=auth_headers(requester),
        json={"title": "Delete me", "description": "...", "priority": "LOW", "reviewer_id": str(reviewer.id)},
    ).json()

    response = client.delete(f"/requests/{created['id']}", headers=auth_headers(requester))
    assert response.status_code == 204


def test_list_reviewers_for_requester(client, make_user, auth_headers):
    requester = make_user(UserRole.REQUESTER)
    make_user(UserRole.REVIEWER, name="Reviewer One")
    make_user(UserRole.REVIEWER, name="Reviewer Two")

    response = client.get("/requests/reviewers", headers=auth_headers(requester))
    assert response.status_code == 200
    assert len(response.json()) == 2
