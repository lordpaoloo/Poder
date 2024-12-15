import re
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

def clean_facebook_url(url):
    # Parse the URL into components
    parsed_url = urlparse(url)
    # Extract query parameters
    query_params = parse_qs(parsed_url.query)
    
    # Keep only essential query parameters for Facebook profile links
    allowed_params = ['id']
    clean_query = {key: value for key, value in query_params.items() if key in allowed_params}
    
    # Rebuild the URL with the cleaned query string
    clean_url = urlunparse((
        parsed_url.scheme,
        parsed_url.netloc,
        parsed_url.path,
        None,  # Clear old query string
        urlencode(clean_query, doseq=True),
        None  # Fragment
    ))
    
    return clean_url

# Example usage
url ="https://www.facebook.com/ThegodfatherMshaker?__cft__[0]=AZUiYVwJpMv_X8DgWNp8iXHdBJG5vvu38Ah4i_z9F_dshf55K3FM4S7QElofG7wZU5NpnxQoMre6E8dP0cskoi49c9TVI6GZTv5QzLUho9SocwgNkfPoWcW-k6FAmLNCVorW3zLcW61sDW258UUCPN8BhmV3_L_tSt5d0RE252wIdTyyc0CZ3yOcx-A-xfTAuPE&__tn__=%3C%2CP-R"

cleaned_url = clean_facebook_url(url)
print(cleaned_url)

