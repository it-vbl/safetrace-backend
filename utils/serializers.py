def custom_response(status, message, data=None, errors=None, override_message=False):
    response = {
        "status": status,
        "message": message,
    }

    if errors:
        response["errors"] = errors
    else:
        response["data"] = data
        if not data and override_message:
            response["message"] = "Data is empty"
    return response
