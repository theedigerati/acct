def get_next_number(model, prefix):
    """
    Generate a valid value for the `number` parameter
    of a model object e.g Invoice, Bill, JournalEntry etc.

    This value is calculated as an increment of 1
    from the id of the latest object in db for the model.

    returns e.g B-000012, INV-000342, JNL-000005
    """
    try:
        latest_object = model._default_manager.latest("id")
        next_number = latest_object.id + 1
        return f"{prefix}-{next_number:06d}"
    except model.DoesNotExist:
        return f"{prefix}-000001"
