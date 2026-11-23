import json
from flask import (
    Response,
    Flask,
    request,
)
from werkzeug.exceptions import (
    InternalServerError,
)

# First try importing via site-packages path, then try directly from "src"
try:
    from autopatch.tools.logger import logger
    from autopatch.debranding import find_config_branch
    from autopatch.debrand_job import enqueue
    from autopatch.tools.webserv_tools import (
        auth_key_required,
        jsonify_response,
        get_name_from_payload,
        get_branch_from_payload,
        get_pushed_branch,
        get_merge_source_branch,
    )
    from autopatch.tools.branch import (
        resolve_upstream_branch,
        is_config_branch,
    )
    import autopatch.tools.slack as tools_slack
except ImportError:
    from tools.logger import logger
    from debranding import find_config_branch
    from debrand_job import enqueue
    from tools.webserv_tools import (
        auth_key_required,
        jsonify_response,
        get_name_from_payload,
        get_branch_from_payload,
        get_pushed_branch,
        get_merge_source_branch,
    )
    from tools.branch import (
        resolve_upstream_branch,
        is_config_branch,
    )
    import tools.slack as tools_slack

app = Flask('almalinux-debranding-tool')

HTTP_200_OK = 200
HTTP_400_BAD_REQUEST = 400

QUEUED = "Debranding queued"


def _queue(
    package: str,
    upstream_branch: str,
    target_branch: str = "",
    report_branch: str = "",
):
    """Queue a debranding job and build the webhook answer.

    The debranding itself runs in a background job (see debrand_job): it can
    take minutes, longer than gunicorn lets a request live. Only the cheap
    check whether the package has a config for the branch runs here, so a
    push of a package without one answers at once and starts nothing.
    """
    _, not_modified = find_config_branch(
        package, upstream_branch, target_branch,
    )
    if not_modified:
        return jsonify_response(
            result={'message': not_modified},
            status_code=HTTP_200_OK,
        )
    enqueue(
        package,
        upstream_branch,
        target_branch=target_branch,
        report_branch=report_branch,
    )
    return jsonify_response(
        result={'message': QUEUED},
        status_code=HTTP_200_OK,
    )


@app.route(
    '/debrand_packages',
    methods=('POST',),
)
@auth_key_required
def debrand_packages():
    # Bound before the try so the except block can always report the failure:
    # anything raised while parsing the payload would otherwise leave these
    # unset and turn the handler itself into an UnboundLocalError, losing both
    # the Slack notification and the agent launch below.
    repo_name = ''
    branch = ''
    try:
        logger.debug(json.dumps(request.json, indent=4))

        repo_name = get_name_from_payload(request.json)
        branch = get_branch_from_payload(request.json)

        if branch.startswith('a'):
            return jsonify_response(
                result={
                    'message': f'Nothing to sync, because it is modified branch',
                    'details': f'branch - {branch}'
                },
                status_code=HTTP_200_OK,
                success=False,
            )

        if not repo_name or not branch:
            return jsonify_response(
                result={
                    'message': f'Nothing to sync, because repository name or branch are absent in payload',
                    'details': f'repo name - {repo_name}, branch - {branch}'
                },
                status_code=HTTP_200_OK,
                success=False,
            )

        return _queue(repo_name, branch, report_branch=branch)
    except Exception as err:
        # Only the config lookup and the job launch run here; a failure of
        # the debranding itself is reported by the job.
        logger.error(err)
        tools_slack.failed_message(repo_name, branch, str(err))
        return jsonify_response(
            result={'message': str(err)},
            status_code=HTTP_200_OK,
            success=False,
        )


@app.route(
    '/autopatch_config_pushed',
    methods=('POST',),
)
@auth_key_required
def autopatch_config_pushed():
    """Restart debranding when a config branch is pushed in the autopatch namespace.

    Triggered by a Gitea *push* webhook on the autopatch namespace. Any change
    to a config branch (a9, a9-beta, a10s, ...) re-runs the debranding so the
    rpms repo is rebuilt immediately, without waiting for the next upstream
    push. This covers both manual config edits and merged agent-fix PRs (a
    merge is itself a push to the base branch), which is why the dedicated
    ``/autopatch_pr_merged`` endpoint is no longer needed.

    Non-config branches are intentionally ignored: this is what keeps the
    agent's ``agent-fix/*`` working branches from triggering a rebuild before
    their PR is merged.

    The rebuild runs as a background job, like one for an upstream push. A
    failed rebuild launches the recovery agent, so a merged fix that is still
    incomplete gets a follow-up PR instead of only a Slack message.
    """
    package = ''
    config_branch = ''
    try:
        payload = request.json
        logger.debug(json.dumps(payload, indent=4))

        # A branch deletion is delivered as a push with deleted=true; nothing
        # to rebuild in that case.
        if payload.get('deleted'):
            return jsonify_response(
                result={
                    'message': 'Nothing to rebuild, branch was deleted',
                },
                status_code=HTTP_200_OK,
                success=False,
            )

        package = get_name_from_payload(payload)
        config_branch = get_pushed_branch(payload)

        if not package or not config_branch:
            return jsonify_response(
                result={
                    'message': 'Nothing to rebuild, package or branch are absent in payload',
                    'details': f"package - {package}, branch - {config_branch}",
                },
                status_code=HTTP_200_OK,
                success=False,
            )

        # Rebuild only for real config branches (a9, a9-beta, a10s, ...). This
        # ignores upstream import branches (c9), the agent's agent-fix/* working
        # branches and any other feature branches.
        if not is_config_branch(config_branch):
            return jsonify_response(
                result={
                    'message': 'Nothing to rebuild, not an autopatch config branch',
                    'details': f"branch - {config_branch}",
                },
                status_code=HTTP_200_OK,
                success=False,
            )

        # Ignore merges between config branches (e.g. forward-merging a9-beta
        # into a9): the fix already triggered a rebuild on the source branch.
        # Merges from non-config branches (agent-fix/*) and plain direct pushes
        # are not affected.
        merge_source = get_merge_source_branch(payload)
        if merge_source and is_config_branch(merge_source):
            return jsonify_response(
                result={
                    'message': 'Nothing to rebuild, merge between config branches',
                    'details': f"merge from {merge_source} into {config_branch}",
                },
                status_code=HTTP_200_OK,
                success=False,
            )

        upstream_branch = resolve_upstream_branch(config_branch)
        logger.info(
            "Config pushed for %s on %s, restarting debranding from upstream %s",
            package, config_branch, upstream_branch,
        )

        return _queue(
            package,
            upstream_branch,
            target_branch=config_branch,
            report_branch=config_branch,
        )
    except Exception as err:
        logger.error(err)
        tools_slack.failed_message(package, config_branch, str(err))
        return jsonify_response(
            result={'message': str(err)},
            status_code=HTTP_200_OK,
            success=False,
        )


@app.errorhandler(InternalServerError)
def handle_internal_server_error(
    error: InternalServerError
) -> Response:
    logger.exception(error)
    return jsonify_response(
        result={
            'message': 'Internal server error',
            'details': str(error),
        },
        status_code=error.code,
    )

if __name__ == '__main__':
    app.run(
        debug=True,
        host='0.0.0.0',
        port=8080,
    )
