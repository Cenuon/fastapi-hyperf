from typing import Annotated, Any

from fastapi import Depends
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth.oauth.dependencies import get_google_provider, get_oauth_state_storage
from app.core.auth.oauth.provider import AbstractOAuthProvider
from app.core.auth.oauth.schemas import OAuthState
from app.core.auth.session.dependencies import (
    get_current_session_data,
    get_current_superuser,
    get_current_user,
    get_optional_user,
    get_session_from_cookie,
    get_session_manager,
)
from app.core.auth.session.manager import SessionManager
from app.core.auth.session.schemas import SessionData
from app.core.auth.session.storage import AbstractSessionStorage
from app.core.db.session import async_session

# Database
AsyncSessionDep = Annotated[AsyncSession, Depends(async_session)]

# Users
CurrentUserDep = Annotated[dict[str, Any], Depends(get_current_user)]
CurrentSuperUserDep = Annotated[dict[str, Any], Depends(get_current_superuser)]
OptionalUserDep = Annotated[dict[str, Any] | None, Depends(get_optional_user)]

# Sessions
SessionManagerDep = Annotated[SessionManager, Depends(get_session_manager)]
CurrentSessionDataDep = Annotated[SessionData, Depends(get_current_session_data)]
OptionalSessionDataDep = Annotated[SessionData | None, Depends(get_session_from_cookie)]

# OAuth
OAuth2FormDep = Annotated[OAuth2PasswordRequestForm, Depends()]
GoogleOAuthProviderDep = Annotated[AbstractOAuthProvider, Depends(get_google_provider)]
OAuthStateStorageDep = Annotated[AbstractSessionStorage[OAuthState], Depends(get_oauth_state_storage)]
