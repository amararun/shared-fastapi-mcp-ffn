from examples.shared.apps.items import app # The FastAPI app
from examples.shared.setup import setup_logging

from fastapi_mcp import FastApiMCP

setup_logging()

# Add MCP server to the FastAPI app
mcp = FastApiMCP(app)

# Mount the MCP server to the FastAPI app
mcp.mount()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)



    ----
    
"""
This example shows how to describe the full response schema instead of just a response example.
"""
from examples.shared.apps.items import app # The FastAPI app
from examples.shared.setup import setup_logging

from fastapi_mcp import FastApiMCP

setup_logging()

# Add MCP server to the FastAPI app
mcp = FastApiMCP(
    app,
    name="Item API MCP",
    description="MCP server for the Item API",
    describe_full_response_schema=True,  # Describe the full response JSON-schema instead of just a response example
    describe_all_responses=True,  # Describe all the possible responses instead of just the success (2XX) response
)

mcp.mount()

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(app, host="0.0.0.0", port=8000)


    ---

    """
This example shows how to customize exposing endpoints by filtering operation IDs and tags.
Notes on filtering:
- You cannot use both `include_operations` and `exclude_operations` at the same time
- You cannot use both `include_tags` and `exclude_tags` at the same time
- You can combine operation filtering with tag filtering (e.g., use `include_operations` with `include_tags`)
- When combining filters, a greedy approach will be taken. Endpoints matching either criteria will be included
"""
from examples.shared.apps.items import app # The FastAPI app
from examples.shared.setup import setup_logging

from fastapi_mcp import FastApiMCP

setup_logging()

# Examples demonstrating how to filter MCP tools by operation IDs and tags

# Filter by including specific operation IDs
include_operations_mcp = FastApiMCP(
    app,
    name="Item API MCP - Included Operations",
    include_operations=["get_item", "list_items"],
)

# Filter by excluding specific operation IDs
exclude_operations_mcp = FastApiMCP(
    app,    
    name="Item API MCP - Excluded Operations",
    exclude_operations=["create_item", "update_item", "delete_item"],
)

# Filter by including specific tags
include_tags_mcp = FastApiMCP(
    app,
    name="Item API MCP - Included Tags",
    include_tags=["items"],
)

# Filter by excluding specific tags
exclude_tags_mcp = FastApiMCP(
    app,
    name="Item API MCP - Excluded Tags",
    exclude_tags=["search"],
)

# Combine operation IDs and tags (include mode)
combined_include_mcp = FastApiMCP(
    app,
    name="Item API MCP - Combined Include",
    include_operations=["delete_item"],
    include_tags=["search"],
)

# Mount all MCP servers with different paths
include_operations_mcp.mount(mount_path="/include-operations-mcp")
exclude_operations_mcp.mount(mount_path="/exclude-operations-mcp")
include_tags_mcp.mount(mount_path="/include-tags-mcp")
exclude_tags_mcp.mount(mount_path="/exclude-tags-mcp")
combined_include_mcp.mount(mount_path="/combined-include-mcp")

if __name__ == "__main__":
    import uvicorn

    print("Server is running with multiple MCP endpoints:")
    print(" - /include-operations-mcp: Only get_item and list_items operations")
    print(" - /exclude-operations-mcp: All operations except create_item, update_item, and delete_item")
    print(" - /include-tags-mcp: Only operations with the 'items' tag")
    print(" - /exclude-tags-mcp: All operations except those with the 'search' tag")
    print(" - /combined-include-mcp: Operations with 'search' tag or delete_item operation")
    uvicorn.run(app, host="0.0.0.0", port=8000)

    """
This example shows how to run the MCP server and the FastAPI app separately.
You can create an MCP server from one FastAPI app, and mount it to a different app.
"""
from fastapi import FastAPI

from examples.shared.apps.items import app
from examples.shared.setup import setup_logging

from fastapi_mcp import FastApiMCP

setup_logging()

MCP_SERVER_HOST = "localhost"
MCP_SERVER_PORT = 8000
ITEMS_API_HOST = "localhost"
ITEMS_API_PORT = 8001


# Take the FastAPI app only as a source for MCP server generation
mcp = FastApiMCP(app)

# Mount the MCP server to a separate FastAPI app
mcp_app = FastAPI()
mcp.mount(mcp_app)

# Run the MCP server separately from the original FastAPI app.
# It still works 🚀
# Your original API is **not exposed**, only via the MCP server.
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(mcp_app, host="0.0.0.0", port=8000)

    """
This example shows how to re-register tools if you add endpoints after the MCP server was created.
"""
from examples.shared.apps.items import app # The FastAPI app
from examples.shared.setup import setup_logging

from fastapi_mcp import FastApiMCP

setup_logging()

mcp = FastApiMCP(app) # Add MCP server to the FastAPI app
mcp.mount() # MCP server


# This endpoint will not be registered as a tool, since it was added after the MCP instance was created
@app.get("/new/endpoint/", operation_id="new_endpoint", response_model=dict[str, str])
async def new_endpoint():
    return {"message": "Hello, world!"}


# But if you re-run the setup, the new endpoints will now be exposed.
mcp.setup_server()


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(app, host="0.0.0.0", port=8000)

    """
This example shows how to mount the MCP server to a specific APIRouter, giving a custom mount path.
"""
from examples.shared.apps.items import app # The FastAPI app
from examples.shared.setup import setup_logging

from fastapi import APIRouter
from fastapi_mcp import FastApiMCP

setup_logging()

other_router = APIRouter(prefix="/other/route")    
app.include_router(other_router)

mcp = FastApiMCP(app)

# Mount the MCP server to a specific router.
# It will now only be available at `/other/route/mcp`
mcp.mount(other_router)


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(app, host="0.0.0.0", port=8000)

    """
This example shows how to configure the HTTP client timeout for the MCP server.
In case you have API endpoints that take longer than 5 seconds to respond, you can increase the timeout.
"""
from examples.shared.apps.items import app # The FastAPI app
from examples.shared.setup import setup_logging

import httpx

from fastapi_mcp import FastApiMCP

setup_logging()


mcp = FastApiMCP(
    app,
    http_client=httpx.AsyncClient(timeout=20)
)
mcp.mount()


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(app, host="0.0.0.0", port=8000)

    """
This example shows how to reject any request without a valid token passed in the Authorization header.

In order to configure the auth header, the config file for the MCP server should looks like this:
```json
{
  "mcpServers": {
    "remote-example": {
      "command": "npx",
      "args": [
        "mcp-remote",
        "http://localhost:8000/mcp",
        "--header",
        "Authorization:${AUTH_HEADER}"
      ]
    },
    "env": {
      "AUTH_HEADER": "Bearer <your-token>"
    }
  }
}
```
"""
from examples.shared.apps.items import app # The FastAPI app
from examples.shared.setup import setup_logging

from fastapi import Depends
from fastapi.security import HTTPBearer

from fastapi_mcp import FastApiMCP, AuthConfig

setup_logging()

# Scheme for the Authorization header
token_auth_scheme = HTTPBearer()

# Create a private endpoint
@app.get("/private")
async def private(token = Depends(token_auth_scheme)):
    return token.credentials

# Create the MCP server with the token auth scheme
mcp = FastApiMCP(
    app,
    name="Protected MCP",
    auth_config=AuthConfig(
        dependencies=[Depends(token_auth_scheme)],
    ),
)

# Mount the MCP server
mcp.mount()


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(app, host="0.0.0.0", port=8000)


    from fastapi import FastAPI, Depends, HTTPException, Request, status
from pydantic_settings import BaseSettings
from typing import Any
import logging

from fastapi_mcp import FastApiMCP, AuthConfig

from examples.shared.auth import fetch_jwks_public_key
from examples.shared.setup import setup_logging


setup_logging()
logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    """
    For this to work, you need an .env file in the root of the project with the following variables:
    AUTH0_DOMAIN=your-tenant.auth0.com
    AUTH0_AUDIENCE=https://your-tenant.auth0.com/api/v2/
    AUTH0_CLIENT_ID=your-client-id
    AUTH0_CLIENT_SECRET=your-client-secret
    """

    auth0_domain: str  # Auth0 domain, e.g. "your-tenant.auth0.com"
    auth0_audience: str  # Audience, e.g. "https://your-tenant.auth0.com/api/v2/"
    auth0_client_id: str
    auth0_client_secret: str

    @property
    def auth0_jwks_url(self):
        return f"https://{self.auth0_domain}/.well-known/jwks.json"

    @property
    def auth0_oauth_metadata_url(self):
        return f"https://{self.auth0_domain}/.well-known/openid-configuration"

    class Config:
        env_file = ".env"


settings = Settings()  # type: ignore


async def lifespan(app: FastAPI):
    app.state.jwks_public_key = await fetch_jwks_public_key(settings.auth0_jwks_url)
    logger.info(f"Auth0 client ID in settings: {settings.auth0_client_id}")
    logger.info(f"Auth0 domain in settings: {settings.auth0_domain}")
    logger.info(f"Auth0 audience in settings: {settings.auth0_audience}")
    yield


async def verify_auth(request: Request) -> dict[str, Any]:
    try:
        import jwt

        auth_header = request.headers.get("authorization", "")
        if not auth_header.startswith("Bearer "):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authorization header")

        token = auth_header.split(" ")[1]

        header = jwt.get_unverified_header(token)

        # Check if this is a JWE token (encrypted token)
        if header.get("alg") == "dir" and header.get("enc") == "A256GCM":
            raise ValueError(
                "Token is encrypted, offline validation not possible. "
                "This is usually due to not specifying the audience when requesting the token."
            )

        # Otherwise, it's a JWT, we can validate it offline
        if header.get("alg") in ["RS256", "HS256"]:
            claims = jwt.decode(
                token,
                app.state.jwks_public_key,
                algorithms=["RS256", "HS256"],
                audience=settings.auth0_audience,
                issuer=f"https://{settings.auth0_domain}/",
                options={"verify_signature": True},
            )
            return claims

    except Exception as e:
        logger.error(f"Auth error: {str(e)}")

    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")


async def get_current_user_id(claims: dict = Depends(verify_auth)) -> str:
    user_id = claims.get("sub")

    if not user_id:
        logger.error("No user ID found in token")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")

    return user_id


app = FastAPI(lifespan=lifespan)


@app.get("/api/public", operation_id="public")
async def public():
    return {"message": "This is a public route"}


@app.get("/api/protected", operation_id="protected")
async def protected(user_id: str = Depends(get_current_user_id)):
    return {"message": f"Hello, {user_id}!", "user_id": user_id}


# Set up FastAPI-MCP with Auth0 auth
mcp = FastApiMCP(
    app,
    name="MCP With Auth0",
    description="Example of FastAPI-MCP with Auth0 authentication",
    auth_config=AuthConfig(
        issuer=f"https://{settings.auth0_domain}/",
        authorize_url=f"https://{settings.auth0_domain}/authorize",
        oauth_metadata_url=settings.auth0_oauth_metadata_url,
        audience=settings.auth0_audience,
        client_id=settings.auth0_client_id,
        client_secret=settings.auth0_client_secret,
        dependencies=[Depends(verify_auth)],
        setup_proxies=True,
    ),
)

# Mount the MCP server
mcp.mount()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)