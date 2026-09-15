from server.shared_view import *

def index(request: HttpRequest) -> HttpResponse:
    """
    Handles the HTTP request for the index view.

    This view renders the "shared/raider.html" template and sets the necessary
    CORS (Cross-Origin Resource Sharing) headers to allow requests from any origin.

    Args:
        request: The HTTP request object.

    Returns:
        HttpResponse: The HTTP response object with the rendered template and CORS headers.
    """
    template_name = request.GET.get("template", "test.html")
    if template_name == "clobber_payload":
        return clobber_payload(request)
    response = render(request, f"shared/{template_name}")
    response['Content-Security-Policy-Report-Only'] = "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self'; connect-src 'self'; font-src 'self'; frame-src 'self'; object-src 'self'; media-src 'self'; manifest-src 'none'; child-src 'self'; script-src-attr 'self'; style-src-attr 'self'; worker-src 'none'; base-uri 'self'; form-action 'self'; frame-ancestors 'self'; report-uri /csp; block-all-mixed-content;"
    response["Access-Control-Allow-Origin"] = "*"
    response["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS, HEAD"
    response["Access-Control-Allow-Headers"] = "Authorization, Origin, X-Requested-With, Content-Type, Accept"
    return response

def hook(request: HttpRequest) -> HttpResponse:
    """
    Handles the HTTP request for the hook view.

    This view renders the "shared/raider.html" template and sets the necessary
    CORS (Cross-Origin Resource Sharing) headers to allow requests from any origin.

    Args:
        request: The HTTP request object.

    Returns:
        HttpResponse: The HTTP response object with the rendered template and CORS headers.
    """
    response = render(request, "shared/hook.html")
    response["Access-Control-Allow-Origin"] = "*"
    response["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS, HEAD"
    response["Access-Control-Allow-Headers"] = "Authorization, Origin, X-Requested-With, Content-Type, Accept"
    return response

def mutation(request: HttpRequest) -> HttpResponse:
    """
    Handles the HTTP request for the mutation view.

    This view renders the "shared/raider.html" template and sets the necessary
    CORS (Cross-Origin Resource Sharing) headers to allow requests from any origin.

    Args:
        request: The HTTP request object.

    Returns:
        HttpResponse: The HTTP response object with the rendered template and CORS headers.
    """
    response = render(request, "shared/mutation.html")
    response["Access-Control-Allow-Origin"] = "*"
    response["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS, HEAD"
    response["Access-Control-Allow-Headers"] = "Authorization, Origin, X-Requested-With, Content-Type, Accept"
    return response
