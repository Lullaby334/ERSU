import os
from pathlib import Path

import pytest

# Configure the application to use a local SQLite database for tests
TEST_DB_PATH = Path(__file__).resolve().parent / 'test_app.sqlite'
os.environ.setdefault('SECRET_KEY', 'test-secret-key')
os.environ['DATABASE_URL'] = f"sqlite:///{TEST_DB_PATH.as_posix()}"

import app as app_module  # noqa: E402


@pytest.fixture(autouse=True)
def fake_templates(monkeypatch):
    """Avoid dependency on real template files during tests."""

    def _fake_render(template_name, **context):
        return f"TEMPLATE:{template_name}"

    monkeypatch.setattr(app_module, 'render_template', _fake_render)


@pytest.fixture()
def app_ctx():
    app_module.app.config.update(TESTING=True)
    with app_module.app.app_context():
        app_module.db.session.remove()
        app_module.db.drop_all()
        app_module.db.create_all()
        yield app_module
        app_module.db.session.remove()
        app_module.db.drop_all()


@pytest.fixture()
def client(app_ctx):
    return app_ctx.app.test_client()


@pytest.fixture()
def db_session(app_ctx):
    return app_ctx.db.session


@pytest.fixture()
def make_user(app_ctx, db_session):
    def _make_user(
        email: str,
        password: str = 'test123',
        full_name: str = 'Test User',
        role: str = None,
        is_active_account: bool = True,
    ):
        role = role or app_ctx.Role.STUDENT
        user = app_ctx.User(
            full_name=full_name,
            email=email,
            role=role,
            is_active_account=is_active_account,
        )
        user.set_password(password)
        db_session.add(user)
        db_session.commit()
        return user

    return _make_user


@pytest.fixture()
def make_equipment(app_ctx, db_session):
    def _make_equipment(
        name: str = 'Oscyloskop Tektronix',
        category: str = 'Pomiary',
        laboratory: str = 'Laboratorium Elektroniki',
        serial_number: str = 'OSC-001',
        status: str = None,
    ):
        status = status or app_ctx.EquipmentStatus.AVAILABLE
        item = app_ctx.Equipment(
            name=name,
            category=category,
            laboratory=laboratory,
            serial_number=serial_number,
            status=status,
        )
        db_session.add(item)
        db_session.commit()
        return item

    return _make_equipment


@pytest.fixture()
def login(client):
    def _login(email: str, password: str = 'test123', follow_redirects: bool = False):
        return client.post(
            '/login',
            data={'email': email, 'password': password},
            follow_redirects=follow_redirects,
        )

    return _login
