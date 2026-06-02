import json
import os
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
    from autopatch.debranding import (
        apply_modifications,
        SUCCESS
    )
    from autopatch.tools.webserv_tools import (
        auth_key_required,
        jsonify_response,
        get_name_from_payload,
        get_branch_from_payload,
        get_pushed_branch,
    )
    from autopatch.tools.branch import (
        resolve_upstream_branch,
        is_config_branch,
    )
    import autopatch.tools.slack as tools_slack
except ImportError:
    from tools.logger import logger
    from debranding import (
        apply_modifications,
        SUCCESS
    )
    from tools.webserv_tools import (
        auth_key_required,
        jsonify_response,
        get_name_from_payload,
        get_branch_from_payload,
        get_pushed_branch,
    )
    from tools.branch import (
        resolve_upstream_branch,
        is_config_branch,
    )
    import tools.slack as tools_slack

app = Flask('almalinux-debranding-tool')

HTTP_200_OK = 200
HTTP_400_BAD_REQUEST = 400

@app.route(
    '/debrand_packages',
    methods=('POST',),
)
@auth_key_required
def debrand_packages():
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

        result = apply_modifications(
            repo_name,
            branch,
        )
        if result == SUCCESS:
            tools_slack.success_message(repo_name, branch)

        return jsonify_response(
            result={
                'message': result,
            },
            status_code=HTTP_200_OK,
        )
    except Exception as err:
        logger.error(err)
        tools_slack.failed_message(repo_name, branch, str(err))
        if os.environ.get("AGENT_ENABLED", "").lower() == "true":
            try:
                from agent_handler import fire_agent
            except ImportError:
                from autopatch.agent_handler import fire_agent
            try:
                agent_pid = fire_agent(repo_name, branch, err)
                if agent_pid:
                    logger.info("Agent launched: pid %s", agent_pid)
            except Exception as agent_err:
                logger.error("Agent launch failed: %s", agent_err)
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

        upstream_branch = resolve_upstream_branch(config_branch)
        logger.info(
            "Config pushed for %s on %s, restarting debranding from upstream %s",
            package, config_branch, upstream_branch,
        )

        result = apply_modifications(
            package,
            upstream_branch,
            target_branch=config_branch,
        )
        if result == SUCCESS:
            tools_slack.success_message(package, config_branch)

        return jsonify_response(
            result={
                'message': result,
            },
            status_code=HTTP_200_OK,
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
