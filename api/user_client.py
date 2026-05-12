"""User and directory API client."""

from pydantic import BaseModel, ConfigDict

from api.base_client import BaseClient


class UserResponse(BaseModel):
    """User profile response."""

    model_config = ConfigDict(extra="allow")

    id: str | int
    name: str | None = None
    email: str | None = None
    department: str | None = None


class UsersListResponse(BaseModel):
    """Paginated users response."""

    model_config = ConfigDict(extra="allow")

    data: list[UserResponse] | None = None
    items: list[UserResponse] | None = None
    total: int | None = None
    page: int | None = None
    limit: int | None = None


class UserClient(BaseClient):
    """Client for directory user endpoints."""

    async def list_users(self, search: str | None = None, expected_status: int = 200) -> UsersListResponse:
        """Return paginated users, optionally filtered by search."""

        params = {"search": search} if search else None
        return await self.get("/users", params=params, expected_status=expected_status, schema=UsersListResponse)

    async def get_user(self, user_id: str | int, expected_status: int = 200) -> UserResponse:
        """Return a single user by id."""

        return await self.get(f"/users/{user_id}", expected_status=expected_status, schema=UserResponse)

