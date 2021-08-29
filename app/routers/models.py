import json
from typing import Optional, List
from datetime import datetime

from fastapi import Depends, HTTPException, Query, APIRouter
from sqlmodel import Session, select

from .items import Item, ItemRead
from ..dependencies import engine, get_session
from ..config import settings

router = APIRouter()


if settings.read_model_items_enabled:

    @router.get(
        "/{model_name}",
        response_model=List[ItemRead],
    )
    async def read_model_items(
        *,
        session: Session = Depends(get_session),
        model_name: str,
        show_deleted: bool = settings.read_model_items_show_deleted_default,
        offset: int = 0,
        limit: int = Query(default=100, lte=100),
    ):
        """
        **List all items of a particular model**

        Selects and lists all models of a particular type.
        """
        query = (
            select(Item) if show_deleted else select(Item).where(Item.deleted != True)
        )

        # Hack: Convert the string instances of data to dicts so the response_model will work.
        # TODO: Fix this.
        model_items = []
        for model_item in session.exec(query.offset(offset).limit(limit)).all():
            model_item.data = json.loads(model_item.data)
            model_items.append(model_item)

        return model_items


if settings.create_model_item_enabled:

    @router.post("/{model_name}", response_model=ItemRead)
    async def create_model_item(
        *,
        session: Session = Depends(get_session),
        model_name: str,
        post_data: dict,
        version: float = settings.create_model_item_version_default,
    ):
        """
        **Create an item with the model name in the URL**

        This endpoint is useful when you don't want to specify all the required fields required by the root POST endpoint.
        Use this when you want to send a completely schema free body in your request.

        The model name specified in the URL will be used as the model name, and the optional version query param can be used
        to set the version being used.

        The created datetime will be added automatically.
        """
        item = Item(
            model=model_name, version=version, data=post_data, created=datetime.now()
        )
        session.add(item)
        session.commit()
        session.refresh(item)

        # Hack: Convert the string instance of data to dict so the response_model will work.
        # TODO: Fix this.
        item.data = json.loads(item.data)
        return item