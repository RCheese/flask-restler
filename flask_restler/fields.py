import datetime as dt

import marshmallow as ma


class Timestamp(ma.fields.Field):
    default_error_messages = {"invalid": "Not a valid timestamp."}

    def _serialize(self, value, attr, obj):
        """Serialize given datetime to timestamp."""
        if value is None:
            return None

        return int(datetime_to_timestamp(value))

    def _deserialize(self, value, attr, data):
        if not value:  # Falsy values, e.g. '', None, [] are not valid
            raise self.fail("invalid")

        try:
            return dt.datetime.utcfromtimestamp(float(value))
        except ValueError:
            raise self.fail("invalid")


class MSTimestamp(Timestamp):
    def _serialize(self, value, *args):
        """Serialize given datetime to timestamp."""
        if value is not None:
            value = super(MSTimestamp, self)._serialize(value, *args) * 1e3
        return value

    def _deserialize(self, value, *args):
        if value:
            value = int(value) / 1e3

        return super(MSTimestamp, self)._deserialize(value, *args)


def datetime_to_timestamp(dt_):
    """Convert given datetime object to timestamp in seconds."""
    return dt_.replace(tzinfo=dt.timezone.utc).timestamp()
