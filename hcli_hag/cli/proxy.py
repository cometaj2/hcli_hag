import os
import sys
from falcon import Request, Response


class HagProxy:
    def __init__(self, app):
        self.app = app

    # Handle common methods; add on_put/on_head if needed for Git
    def on_get(self, req: Request, resp: Response, path: str = ''):
        self._proxy(req, resp, path)

    def on_post(self, req: Request, resp: Response, path: str = ''):
        self._proxy(req, resp, path)

    def _proxy(self, req: Request, resp: Response, path: str = ''):
        # Build WSGI environ from Falcon req (Falcon runs on WSGI, so req.env is available)
        environ = req.env.copy()

#         # Adjust PATH_INFO to what Dulwich expects (e.g., '/myrepo.git/info/refs')
#         # The route is '/repos/{path:segments}', so path is 'myrepo.git/info/refs'
#         path_info = '/' + path if path else ''
#         if req.query_string:
#             path_info += '?' + req.query_string
# 
#         environ['PATH_INFO'] = path_info
#         environ['REQUEST_METHOD'] = req.method
#         environ['CONTENT_LENGTH'] = str(req.content_length or 0)
#         environ['CONTENT_TYPE'] = req.content_type or ''
#         environ['wsgi.input'] = req.stream
#         environ['wsgi.errors'] = req.env['wsgi.errors']  # Reuse for logging
# 
#         # Add HTTP headers to environ
#         for name, value in req.headers.items():
#             name = name.upper().replace('-', '_')
#             if name not in ('CONTENT_TYPE', 'CONTENT_LENGTH'):
#                 name = 'HTTP_' + name
#             environ[name] = value

        # Collect response parts
        body_parts = []
        headers_set = []

        def start_response(status, response_headers, exc_info=None):
            resp.status = status  # e.g., '200 OK'
            for name, value in response_headers:
                resp.set_header(name, value)
            headers_set.extend(response_headers)
            if exc_info:
                raise exc_info[0].with_traceback(exc_info[1], exc_info[2])

        # Call Dulwich WSGI app
        result = self.app(environ, start_response)

        # Collect body
        for data in result:
            body_parts.append(data)

        resp.text = b''.join(body_parts)

        # Close if iterable has close()
        if hasattr(result, 'close'):
            result.close()
