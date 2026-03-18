from flask import jsonify


def ok(data=None, message: str = "", status_code: int = 200, **extra):
    payload = {"success": True, "data": data}
    if message:
        payload["message"] = message
    payload.update(extra)
    return jsonify(payload), status_code


def fail(message: str, status_code: int = 400, **extra):
    payload = {"success": False, "message": message}
    payload.update(extra)
    return jsonify(payload), status_code

