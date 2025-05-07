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
    from autopatch.debranding import (
        apply_modifications,
        SUCCESS
    )
    from autopatch.tools.webserv_tools import (
        auth_key_required,
        jsonify_response,
        get_name_from_payload,
        get_branch_from_payload,
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
