import peewee as pw
import datetime as dt
import marshmallow as ma
from playhouse.db_url import connect


database = connect("sqlite:///:memory:")


class Role(pw.Model):

    name = pw.CharField(255, default="user")

    class Meta:
        database = database


class User(pw.Model):

    created = pw.DateTimeField(default=dt.datetime.utcnow)
    login = pw.CharField(255)
    name = pw.CharField(255, null=True)
    password = pw.CharField(127, null=True)
    is_active = pw.BooleanField(default=True)

    role = pw.ForeignKeyField(Role, null=True)

    class Meta:
        database = database


database.create_tables([User, Role], safe=True)


def test_resource(app, api, client):
    from flask_restler.peewee import ModelResource

    @api.route
    class UserResouce(ModelResource):

        methods = "get", "post", "put", "delete"

        class Meta:
            model = User
            filters = "name", "login"
            schema_exclude = ("password",)
            sorting = "login", User.name

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
    assert response.json["id"]

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
        },
    )

    response = client.post_json(
        "/api/v1/user",
        {
            "login": "zigmund",
            "name": "Zigmund McTest",
        },
    )

    response = client.get("/api/v1/user")
    assert len(response.json) == 3

    response = client.get("/api/v1/user?sort=login")
    assert response.json[0]["login"] == "dave"

    response = client.get("/api/v1/user?sort=name")
    assert response.json[0]["login"] == "mike"

    response = client.get("/api/v1/user?sort=-login")
    assert response.json[0]["login"] == "zigmund"

    response = client.get('/api/v1/user?where={"login": "dave"}')
    assert len(response.json) == 1
    assert response.json[0]["login"] == "dave"

    response = client.delete("/api/v1/user/1")
    assert not response.json

    response = client.get("/api/v1/user")
    assert len(response.json) == 2

    response = client.get("/api/v1/_specs")
    assert response.json


def test_custom_converter(app, api, client):
    from flask_restler.peewee import ModelResource
    from marshmallow_peewee.convert import ModelConverter

    class CustomConverter(ModelConverter):
        def convert_BooleanField(self, field, validate=None, **params):
            return ma.fields.Int(**params)

    @api.route
    class UserResouce(ModelResource):

        methods = "get", "post", "put", "delete"

        class Meta:
            model = User
            models_converter = CustomConverter
            filters = "name", "login"
            schema_exclude = ("password",)
            sorting = ("login",)

    response = client.get("/api/v1/user")
    assert response.json[0]["is_active"] is 1
