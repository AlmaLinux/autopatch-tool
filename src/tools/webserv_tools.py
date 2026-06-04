import hmac
import os
import re
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


# Head-commit messages produced by a branch merge. Push webhooks carry no
# structured merge metadata, so the source branch is recovered from the
# message of the head commit:
#   * Gitea PR merge: "Merge pull request '<title>' (#N) from <head> into <base>"
#     where <head> is "owner/repo:branch" (cross-repo) or just "branch".
#   * plain git merge: "Merge branch 'branch' into <base>" / "Merge branch 'branch'".
_PR_MERGE_RE = re.compile(r"^Merge pull request .* from (\S+?)(?: into \S+)?$")
_GIT_MERGE_RE = re.compile(r"^Merge branch '([^']+)'")


def get_merge_source_branch(
    payload: Dict[str, Any]
) -> str:
    """Return the source branch of a merge-commit push, or '' if not a merge.

    Push webhooks don't include PR/merge metadata, so the source branch is
    parsed from the first line of the head commit message. Used to ignore
    merges between config branches (e.g. ``a9-beta`` -> ``a9``) while still
    rebuilding on merges from non-config branches (e.g. ``agent-fix/*``) and
    on plain direct pushes (which have no merge commit -> '').
    """
    head_commit = payload.get('head_commit') or {}
    message = head_commit.get('message') or ''
    first_line = message.splitlines()[0] if message else ''

    pr_match = _PR_MERGE_RE.match(first_line)
    if pr_match:
        # Strip an optional "owner/repo:" prefix; the branch is after the colon.
        return pr_match.group(1).split(':')[-1]

    git_match = _GIT_MERGE_RE.match(first_line)
    if git_match:
        return git_match.group(1)

    return ''
