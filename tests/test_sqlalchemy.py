import pytest
import sqlalchemy as sa
from sqlalchemy.ext.declarative import declarative_base


Model = declarative_base()


class Role(Model):

    __tablename__ = "role"

    id = sa.Column(sa.Integer, primary_key=True)
    name = sa.Column(sa.String)


class User(Model):

    __tablename__ = "user"

    id = sa.Column(sa.Integer, primary_key=True)
    login = sa.Column(sa.String)
    name = sa.Column(sa.String)
    password = sa.Column(sa.String)
    role_id = sa.Column(sa.ForeignKey(Role.id))

    role = sa.orm.relationship(Role)


@pytest.fixture(scope="session")
def sa_engine():
    from sqlalchemy import create_engine

    return create_engine("sqlite:///:memory:", echo=True)


@pytest.fixture(scope="session")
def sa_session(sa_engine):
    from sqlalchemy.orm import sessionmaker

    Session = sessionmaker()
    Session.configure(bind=sa_engine)
    return Session()


@pytest.fixture(scope="session", autouse=True)
def migrate(sa_engine):
    Model.metadata.create_all(sa_engine)


def test_resource(app, api, client, sa_session):
    from flask_restler.sqlalchemy import ModelResource, Filter

    @api.route
    class UserResouce(ModelResource):

        methods = "get", "post", "put", "delete"

        class Meta:
            model = User
            session = lambda: sa_session  # noqa
            filters = "login", "name", Filter("role", mfield=Role.name)
            schema_exclude = ("password",)
            sorting = "login", User.name

        def get_many(self, **kwargs):
            """Join on Role for roles filters."""
            return sa_session.query(User).outerjoin(User.role)

    role = Role(name="test")
    sa_session.add(role)
    sa_session.commit()

    response = client.get("/api/v1/user")
    assert not response.json

    response = client.post_json(
        "/api/v1/user",
        {
            "login": "mike",
            "name": "Mike Bacon",
        },
    )
    assert "password" not in response.json
    assert response.json

    response = client.put_json(
        "/api/v1/user/1",
        {
            "name": "Aaron Summer",
        },
    )
    assert response.json["name"] == "Aaron Summer"

    response = client.post_json(
        "/api/v1/user",
        {
            "login": "dave",
            "name": "Dave Macaroff",
            "role": role.id,
        },
    )

    response = client.get("/api/v1/user")
    assert len(response.json) == 2

    response = client.get("/api/v1/user?sort=login,unknown")
    assert response.json[0]["login"] == "dave"

    response = client.get("/api/v1/user?sort=name,login")
    assert response.json[0]["login"] == "mike"

    response = client.get("/api/v1/user?sort=-login")
    assert response.json[0]["login"] == "mike"

    response = client.get('/api/v1/user?where={"login": "dave"}')
    assert len(response.json) == 1
    assert response.json[0]["login"] == "dave"

    response = client.get('/api/v1/user?where={"login": {"$like": "da%"}}')
    assert len(response.json) == 1
    assert response.json[0]["login"] == "dave"

    response = client.delete("/api/v1/user/1")
    assert not response.json

    response = client.get("/api/v1/user")
    assert len(response.json) == 1

    response = client.get('/api/v1/user?where={"role": "test"}')
    assert len(response.json) == 1

    response = client.get('/api/v1/user?where={"role": "unknown"}')
    assert not response.json
