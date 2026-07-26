def model_to_dict(model):
    """Convert an ORM model to the legacy JSON-compatible dictionary shape."""
    data = {}
    for column in model.__table__.columns:
        value = getattr(model, column.name)
        data[column.name] = value.isoformat() if hasattr(value, "isoformat") else value
    return data
