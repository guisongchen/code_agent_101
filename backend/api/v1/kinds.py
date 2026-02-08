"""RESTful API endpoints for CRD resources.

Implements Kubernetes-style REST API for Ghost, Model, Shell, Bot, Team, and Skill resources.

Epic 10: RESTful API Endpoints
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.engine import get_db_session
from backend.schemas import (
    BotCreateRequest,
    BotResponse,
    GhostCreateRequest,
    GhostCRD,
    GhostResponse,
    ModelCreateRequest,
    ModelCRD,
    ModelResponse,
    ShellCreateRequest,
    ShellCRD,
    ShellResponse,
    SkillCreateRequest,
    SkillCRD,
    SkillResponse,
    TeamCreateRequest,
    TeamCRD,
    TeamResponse,
)
from backend.services import (
    BotService,
    GhostService,
    ModelService,
    ShellService,
    SkillService,
    TeamService,
)

router = APIRouter()


# =============================================================================
# Ghost Endpoints
# =============================================================================


@router.post(
    "/kinds/ghosts",
    response_model=GhostResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new Ghost",
    description="Create a new Ghost resource with the specified configuration.",
)
async def create_ghost(
    request: GhostCreateRequest,
    session: AsyncSession = Depends(get_db_session),
) -> GhostResponse:
    """Create a new Ghost resource."""
    service = GhostService(session)

    ghost_crd = GhostCRD(
        metadata=request.metadata,
        spec=request.spec,
    )

    try:
        result = await service.create(ghost_crd, created_by=request.metadata.created_by)
        return result
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))


@router.get(
    "/kinds/ghosts",
    response_model=List[GhostResponse],
    summary="List Ghosts",
    description="List all Ghost resources in the specified namespace.",
)
async def list_ghosts(
    namespace: Optional[str] = Query(default="default", description="Namespace filter (omit for all namespaces)"),
    session: AsyncSession = Depends(get_db_session),
) -> List[GhostResponse]:
    """List Ghost resources."""
    service = GhostService(session)

    if namespace is None:
        return await service.list(include_all_namespaces=True)
    return await service.list(namespace=namespace)


@router.get(
    "/kinds/ghosts/{name}",
    response_model=GhostResponse,
    summary="Get a Ghost",
    description="Get a specific Ghost resource by name.",
)
async def get_ghost(
    name: str,
    namespace: str = Query(default="default", description="Namespace for the resource"),
    session: AsyncSession = Depends(get_db_session),
) -> GhostResponse:
    """Get a Ghost resource by name."""
    service = GhostService(session)
    ghost = await service.get(name, namespace)

    if not ghost:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ghost '{name}' not found in namespace '{namespace}'",
        )
    return ghost


@router.delete(
    "/kinds/ghosts/{name}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a Ghost",
    description="Soft delete a Ghost resource by name.",
)
async def delete_ghost(
    name: str,
    namespace: str = Query(default="default", description="Namespace for the resource"),
    session: AsyncSession = Depends(get_db_session),
) -> None:
    """Delete a Ghost resource."""
    service = GhostService(session)
    deleted = await service.delete(name, namespace)

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ghost '{name}' not found in namespace '{namespace}'",
        )


# =============================================================================
# Model Endpoints
# =============================================================================


@router.post(
    "/kinds/models",
    response_model=ModelResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new Model",
    description="Create a new Model resource with the specified configuration.",
)
async def create_model(
    request: ModelCreateRequest,
    session: AsyncSession = Depends(get_db_session),
) -> ModelResponse:
    """Create a new Model resource."""
    service = ModelService(session)

    model_crd = ModelCRD(
        metadata=request.metadata,
        spec=request.spec,
    )

    try:
        result = await service.create(model_crd, created_by=request.metadata.created_by)
        return result
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))


@router.get(
    "/kinds/models",
    response_model=List[ModelResponse],
    summary="List Models",
    description="List all Model resources in the specified namespace.",
)
async def list_models(
    namespace: Optional[str] = Query(default="default", description="Namespace filter (omit for all namespaces)"),
    session: AsyncSession = Depends(get_db_session),
) -> List[ModelResponse]:
    """List Model resources."""
    service = ModelService(session)

    if namespace is None:
        return await service.list(include_all_namespaces=True)
    return await service.list(namespace=namespace)


@router.get(
    "/kinds/models/{name}",
    response_model=ModelResponse,
    summary="Get a Model",
    description="Get a specific Model resource by name.",
)
async def get_model(
    name: str,
    namespace: str = Query(default="default", description="Namespace for the resource"),
    session: AsyncSession = Depends(get_db_session),
) -> ModelResponse:
    """Get a Model resource by name."""
    service = ModelService(session)
    model = await service.get(name, namespace)

    if not model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Model '{name}' not found in namespace '{namespace}'",
        )
    return model


@router.delete(
    "/kinds/models/{name}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a Model",
    description="Soft delete a Model resource by name.",
)
async def delete_model(
    name: str,
    namespace: str = Query(default="default", description="Namespace for the resource"),
    session: AsyncSession = Depends(get_db_session),
) -> None:
    """Delete a Model resource."""
    service = ModelService(session)
    deleted = await service.delete(name, namespace)

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Model '{name}' not found in namespace '{namespace}'",
        )


# =============================================================================
# Shell Endpoints
# =============================================================================


@router.post(
    "/kinds/shells",
    response_model=ShellResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new Shell",
    description="Create a new Shell resource with the specified configuration.",
)
async def create_shell(
    request: ShellCreateRequest,
    session: AsyncSession = Depends(get_db_session),
) -> ShellResponse:
    """Create a new Shell resource."""
    service = ShellService(session)

    shell_crd = ShellCRD(
        metadata=request.metadata,
        spec=request.spec,
    )

    try:
        result = await service.create(shell_crd, created_by=request.metadata.created_by)
        return result
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))


@router.get(
    "/kinds/shells",
    response_model=List[ShellResponse],
    summary="List Shells",
    description="List all Shell resources in the specified namespace.",
)
async def list_shells(
    namespace: Optional[str] = Query(default="default", description="Namespace filter (omit for all namespaces)"),
    session: AsyncSession = Depends(get_db_session),
) -> List[ShellResponse]:
    """List Shell resources."""
    service = ShellService(session)

    if namespace is None:
        return await service.list(include_all_namespaces=True)
    return await service.list(namespace=namespace)


@router.get(
    "/kinds/shells/{name}",
    response_model=ShellResponse,
    summary="Get a Shell",
    description="Get a specific Shell resource by name.",
)
async def get_shell(
    name: str,
    namespace: str = Query(default="default", description="Namespace for the resource"),
    session: AsyncSession = Depends(get_db_session),
) -> ShellResponse:
    """Get a Shell resource by name."""
    service = ShellService(session)
    shell = await service.get(name, namespace)

    if not shell:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Shell '{name}' not found in namespace '{namespace}'",
        )
    return shell


@router.delete(
    "/kinds/shells/{name}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a Shell",
    description="Soft delete a Shell resource by name.",
)
async def delete_shell(
    name: str,
    namespace: str = Query(default="default", description="Namespace for the resource"),
    session: AsyncSession = Depends(get_db_session),
) -> None:
    """Delete a Shell resource."""
    service = ShellService(session)
    deleted = await service.delete(name, namespace)

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Shell '{name}' not found in namespace '{namespace}'",
        )


# =============================================================================
# Bot Endpoints
# =============================================================================


@router.post(
    "/kinds/bots",
    response_model=BotResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new Bot",
    description="Create a new Bot resource with the specified configuration. Validates that referenced Ghost, Model, and Shell resources exist.",
)
async def create_bot(
    request: BotCreateRequest,
    session: AsyncSession = Depends(get_db_session),
) -> BotResponse:
    """Create a new Bot resource."""
    service = BotService(session)

    from backend.schemas import BotCRD

    bot_crd = BotCRD(
        metadata=request.metadata,
        spec=request.spec,
    )

    try:
        result = await service.create(bot_crd, created_by=request.metadata.created_by)
        return result
    except ValueError as e:
        # Could be duplicate or invalid reference
        if "already exists" in str(e):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get(
    "/kinds/bots",
    response_model=List[BotResponse],
    summary="List Bots",
    description="List all Bot resources in the specified namespace.",
)
async def list_bots(
    namespace: Optional[str] = Query(default="default", description="Namespace filter (omit for all namespaces)"),
    session: AsyncSession = Depends(get_db_session),
) -> List[BotResponse]:
    """List Bot resources."""
    service = BotService(session)

    if namespace is None:
        return await service.list(include_all_namespaces=True)
    return await service.list(namespace=namespace)


@router.get(
    "/kinds/bots/{name}",
    response_model=BotResponse,
    summary="Get a Bot",
    description="Get a specific Bot resource by name.",
)
async def get_bot(
    name: str,
    namespace: str = Query(default="default", description="Namespace for the resource"),
    session: AsyncSession = Depends(get_db_session),
) -> BotResponse:
    """Get a Bot resource by name."""
    service = BotService(session)
    bot = await service.get(name, namespace)

    if not bot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Bot '{name}' not found in namespace '{namespace}'",
        )
    return bot


@router.delete(
    "/kinds/bots/{name}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a Bot",
    description="Soft delete a Bot resource by name.",
)
async def delete_bot(
    name: str,
    namespace: str = Query(default="default", description="Namespace for the resource"),
    session: AsyncSession = Depends(get_db_session),
) -> None:
    """Delete a Bot resource."""
    service = BotService(session)
    deleted = await service.delete(name, namespace)

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Bot '{name}' not found in namespace '{namespace}'",
        )


# =============================================================================
# Team Endpoints
# =============================================================================


@router.post(
    "/kinds/teams",
    response_model=TeamResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new Team",
    description="Create a new Team resource with the specified configuration. Validates that referenced Bot resources exist.",
)
async def create_team(
    request: TeamCreateRequest,
    session: AsyncSession = Depends(get_db_session),
) -> TeamResponse:
    """Create a new Team resource."""
    service = TeamService(session)

    team_crd = TeamCRD(
        metadata=request.metadata,
        spec=request.spec,
    )

    try:
        result = await service.create(team_crd, created_by=request.metadata.created_by)
        return result
    except ValueError as e:
        if "already exists" in str(e):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get(
    "/kinds/teams",
    response_model=List[TeamResponse],
    summary="List Teams",
    description="List all Team resources in the specified namespace.",
)
async def list_teams(
    namespace: Optional[str] = Query(default="default", description="Namespace filter (omit for all namespaces)"),
    session: AsyncSession = Depends(get_db_session),
) -> List[TeamResponse]:
    """List Team resources."""
    service = TeamService(session)

    if namespace is None:
        return await service.list(include_all_namespaces=True)
    return await service.list(namespace=namespace)


@router.get(
    "/kinds/teams/{name}",
    response_model=TeamResponse,
    summary="Get a Team",
    description="Get a specific Team resource by name.",
)
async def get_team(
    name: str,
    namespace: str = Query(default="default", description="Namespace for the resource"),
    session: AsyncSession = Depends(get_db_session),
) -> TeamResponse:
    """Get a Team resource by name."""
    service = TeamService(session)
    team = await service.get(name, namespace)

    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Team '{name}' not found in namespace '{namespace}'",
        )
    return team


@router.delete(
    "/kinds/teams/{name}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a Team",
    description="Soft delete a Team resource by name.",
)
async def delete_team(
    name: str,
    namespace: str = Query(default="default", description="Namespace for the resource"),
    session: AsyncSession = Depends(get_db_session),
) -> None:
    """Delete a Team resource."""
    service = TeamService(session)
    deleted = await service.delete(name, namespace)

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Team '{name}' not found in namespace '{namespace}'",
        )


# =============================================================================
# Skill Endpoints
# =============================================================================


@router.post(
    "/kinds/skills",
    response_model=SkillResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new Skill",
    description="Create a new Skill resource with the specified configuration.",
)
async def create_skill(
    request: SkillCreateRequest,
    session: AsyncSession = Depends(get_db_session),
) -> SkillResponse:
    """Create a new Skill resource."""
    service = SkillService(session)

    skill_crd = SkillCRD(
        metadata=request.metadata,
        spec=request.spec,
    )

    try:
        result = await service.create(skill_crd, created_by=request.metadata.created_by)
        return result
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))


@router.get(
    "/kinds/skills",
    response_model=List[SkillResponse],
    summary="List Skills",
    description="List all Skill resources in the specified namespace.",
)
async def list_skills(
    namespace: Optional[str] = Query(default="default", description="Namespace filter (omit for all namespaces)"),
    session: AsyncSession = Depends(get_db_session),
) -> List[SkillResponse]:
    """List Skill resources."""
    service = SkillService(session)

    if namespace is None:
        return await service.list(include_all_namespaces=True)
    return await service.list(namespace=namespace)


@router.get(
    "/kinds/skills/{name}",
    response_model=SkillResponse,
    summary="Get a Skill",
    description="Get a specific Skill resource by name.",
)
async def get_skill(
    name: str,
    namespace: str = Query(default="default", description="Namespace for the resource"),
    session: AsyncSession = Depends(get_db_session),
) -> SkillResponse:
    """Get a Skill resource by name."""
    service = SkillService(session)
    skill = await service.get(name, namespace)

    if not skill:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Skill '{name}' not found in namespace '{namespace}'",
        )
    return skill


@router.delete(
    "/kinds/skills/{name}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a Skill",
    description="Soft delete a Skill resource by name.",
)
async def delete_skill(
    name: str,
    namespace: str = Query(default="default", description="Namespace for the resource"),
    session: AsyncSession = Depends(get_db_session),
) -> None:
    """Delete a Skill resource."""
    service = SkillService(session)
    deleted = await service.delete(name, namespace)

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Skill '{name}' not found in namespace '{namespace}'",
        )
