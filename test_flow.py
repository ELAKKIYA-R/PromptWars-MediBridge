from google_auth_oauthlib.flow import Flow
import inspect
print("fetch_token signature:", inspect.signature(Flow.fetch_token))
