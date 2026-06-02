import hmac
import os
from functools import wraps
from typing import Dict, Any
from werkzeug.exceptions import (
    Forbidden,
)
from flask import (
    Response,
    make_response,
    jsonify,
    request,
)


def jsonify_response(
    result: Dict[str, Any],
    status_code: int,
    success: bool = True,
) -> Response:
    result['success'] = success
    return make_response(
        jsonify(result),
        status_code,
    )

def auth_key_required(f):
    """
    Decorator: Check auth key
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        real_signature = request.headers.get('X-Gitea-Signature', '')
        calc_signature = hmac.new(
            key=os.environ['AUTH_KEY'].encode(),
            msg=request.data,
            digestmod='SHA256',
        ).hexdigest()
        if real_signature != calc_signature:
            raise Forbidden(
                'Wrong or empty auth key'
            )
        return f(*args, **kwargs)
    return decorated_function


def get_name_from_payload(
    payload: Dict[str, Any]
) -> str:
    if 'repository' in payload:
        if 'name' in payload['repository']:
            return payload['repository']['name']
    return ''


def get_branch_from_payload(
    payload: Dict[str, Any]
) -> str:
    if 'ref' in payload:
        return payload['ref'].split('/')[-2]
    return ''

def get_tag_from_payload(
    payload: Dict[str, Any]
) -> str:
    if 'ref' in payload and 'ref_type' in payload and "tag" == payload['ref_type']:
        return payload['ref']
    return ''

def get_pushed_branch(
    payload: Dict[str, Any]
) -> str:
    """Extract the pushed branch name from a Gitea *push* webhook payload.

    Returns the branch for ``refs/heads/<branch>`` pushes (e.g. ``a9-beta``),
    and '' for tag pushes (``refs/tags/...``) or malformed payloads.
    """
    prefix = 'refs/heads/'
    ref = payload.get('ref', '')
    if ref.startswith(prefix):
        return ref[len(prefix):]
    return ''
