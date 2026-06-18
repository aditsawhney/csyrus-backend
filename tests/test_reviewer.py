from app.models.enums import UserRole


def _create_request(client, auth_headers, requester, reviewer):
    return client.post(
        "/requests",
        headers=auth_headers(requester),
        json={"title": "Leave request", "description": "PTO", "priority": "MEDIUM", "reviewer_id": str(reviewer.id)},
    ).json()


def test_reviewer_sees_only_assigned_requests(client, make_user, auth_headers):
    requester = make_user(UserRole.REQUESTER)
    reviewer_a = make_user(UserRole.REVIEWER)
    reviewer_b = make_user(UserRole.REVIEWER)

    _create_request(client, auth_headers, requester, reviewer_a)

    response = client.get("/reviewer/requests", headers=auth_headers(reviewer_b))
    assert response.status_code == 200
    assert response.json() == []


def test_reviewer_can_approve_assigned_request(client, make_user, auth_headers):
    requester = make_user(UserRole.REQUESTER)
    reviewer = make_user(UserRole.REVIEWER)
    created = _create_request(client, auth_headers, requester, reviewer)

    response = client.post(
        f"/reviewer/requests/{created['id']}/approve",
        headers=auth_headers(reviewer),
        json={"comments": "Looks good"},
    )

    assert response.status_code == 200
    assert response.json()["status"] == "APPROVED"


def test_reviewer_can_reject_assigned_request(client, make_user, auth_headers):
    requester = make_user(UserRole.REQUESTER)
    reviewer = make_user(UserRole.REVIEWER)
    created = _create_request(client, auth_headers, requester, reviewer)

    response = client.post(
        f"/reviewer/requests/{created['id']}/reject",
        headers=auth_headers(reviewer),
        json={"comments": "Missing receipts"},
    )

    assert response.status_code == 200
    assert response.json()["status"] == "REJECTED"


def test_unassigned_reviewer_cannot_act(client, make_user, auth_headers):
    requester = make_user(UserRole.REQUESTER)
    reviewer = make_user(UserRole.REVIEWER)
    other_reviewer = make_user(UserRole.REVIEWER)
    created = _create_request(client, auth_headers, requester, reviewer)

    response = client.post(
        f"/reviewer/requests/{created['id']}/reject",
        headers=auth_headers(other_reviewer),
        json={"comments": "Not mine"},
    )
    assert response.status_code == 403


def test_cannot_review_already_reviewed_request(client, make_user, auth_headers):
    requester = make_user(UserRole.REQUESTER)
    reviewer = make_user(UserRole.REVIEWER)
    created = _create_request(client, auth_headers, requester, reviewer)

    client.post(f"/reviewer/requests/{created['id']}/approve", headers=auth_headers(reviewer), json={"comments": "ok"})

    response = client.post(
        f"/reviewer/requests/{created['id']}/reject",
        headers=auth_headers(reviewer),
        json={"comments": "too late"},
    )
    assert response.status_code == 409


def test_requester_cannot_call_reviewer_endpoints(client, make_user, auth_headers):
    requester = make_user(UserRole.REQUESTER)
    response = client.get("/reviewer/requests", headers=auth_headers(requester))
    assert response.status_code == 403
