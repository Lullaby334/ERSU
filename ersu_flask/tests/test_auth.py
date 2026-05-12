from app import Role, User


def test_register_creates_new_student_user(client, db_session):
    response = client.post(
        '/register',
        data={
            'full_name': 'Jan Kowalski',
            'email': 'jan@example.com',
            'password': 'sekret123',
            'role': Role.STUDENT,
        },
        follow_redirects=False,
    )

    created = db_session.query(User).filter_by(email='jan@example.com').first()

    assert response.status_code == 302
    assert created is not None
    assert created.role == Role.STUDENT
    assert created.check_password('sekret123')



def test_login_rejects_wrong_password(client, make_user):
    make_user('anna@example.com', password='good-pass')

    response = client.post(
        '/login',
        data={'email': 'anna@example.com', 'password': 'bad-pass'},
        follow_redirects=False,
    )

    assert response.status_code == 200
    with client.session_transaction() as session:
        assert '_user_id' not in session



def test_inactive_user_cannot_log_in(client, make_user):
    make_user('blocked@example.com', password='sekret123', is_active_account=False)

    response = client.post(
        '/login',
        data={'email': 'blocked@example.com', 'password': 'sekret123'},
        follow_redirects=False,
    )

    assert response.status_code == 200
    with client.session_transaction() as session:
        assert '_user_id' not in session
