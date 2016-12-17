"""Module to set up the server."""
import socket
import email.utils
import os
import mimetypes
import io


def server():
    """Start server to receive message and echo back."""
    server = socket.socket(socket.AF_INET,
                           socket.SOCK_STREAM,
                           socket.IPPROTO_TCP)
    address = ("127.0.0.1", 5001)
    server.bind(address)
    server.listen(1)
    buffer_length = 8
    while True:
        try:
            conn, addr = server.accept()
            request = ""
            response = ""
            conn.settimeout(1.5)
            try:
                while request[-8:] != '\\r\\n\\r\\n':
                    print(request)
                    request += conn.recv(buffer_length).decode("utf8")
                print('received')
                uri = parse_request(request)
                body, file_type = resolve_uri(uri)
                response = response_ok(body, file_type)
            except ValueError as e:
                response = response_error(e.args[0])
            except socket.timeout:
                pass
            conn.sendall(response.encode("utf8"))
            conn.close()
        except KeyboardInterrupt:
            try:
                conn.close()
            except:
                pass
            break
    server.close()


def response_ok(body, file_type):
    """Set up and return 200 response."""
    headers = {
        "Content-Type": file_type,
        "Date": email.utils.formatdate(usegmt=True),
        "Connection": "close"
    }
    response = "HTTP/1.1 200 OK\r\n"
    for key in sorted(headers.keys()):
        response += key + ': ' + headers[key] + '\r\n'
    response += '\r\n' + body + 'EOF'
    return response


def response_error(phrase):
    """Set up and return an error status code and message."""
    headers = {
        "Content-Type": "text/plain",
        "Date": email.utils.formatdate(usegmt=True),
        "Connection": "close"
    }
    response = "HTTP/1.1 " + phrase + '\r\n'
    for key in headers:
        response += key + ': ' + headers[key] + '\r\n'
    response += 'EOF'
    return response


def parse_request(request):
    """Check the request for good stuff."""
    lst = request.split("\\r\\n")
    try:
        if lst[0].split()[0] != "GET":
            raise ValueError("405 Method Not Allowed: GET only")
        if lst[0].split()[2] != "HTTP/1.1":
            if "HTTP/1.1" in lst[0]:
                raise IndexError
            raise ValueError("400 Bad Request: HTTP/1.1 only")
        headers = parse_headers(lst[1:-2])
        if 'Host' not in headers:
            raise ValueError("400 Bad Request: Host header required")
        if request[-8:] != '\\r\\n\\r\\n':
            raise ValueError("400 Bad Request: Missing final carriage returns")
    except ValueError as e:
        raise e
    except IndexError as e:
        raise ValueError("400 Bad Request: MALFORMED")
    return lst[0].split()[1]


def parse_headers(headers_lst):
    """Parse headers into a dict."""
    headers = {}
    for header in headers_lst:
        try:
            key = header[:header.index(':')]
            value = header[header.index(':'):].strip()
            headers[key] = value
        except ValueError:
            raise IndexError
    return headers


def resolve_uri(uri):
    """Try to return response body."""
    path = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                        'webroot',
                        uri)
    html = "<html><body>{}</body></html>"
    try:
        if os.path.isdir(path):
            body = html.format('<a href=' + uri + '></a>')
        elif os.path.isfile(path):
            f = io.open(path, encoding='utf-8')
            body = html.format(f.read())
            f.close()
        return body, mimetypes.guess_type(uri)[0]
    except Exception:
        raise ValueError("404 File Not Found")














