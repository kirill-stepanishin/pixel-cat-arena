from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.item import ItemInstanceRead, ItemRarity, ItemSlot

MAX_LISTING_PRICE = 1_000_000


class ListingCreate(BaseModel):
    item_id: str
    price: int = Field(gt=0, le=MAX_LISTING_PRICE)


class ListingRead(BaseModel):
    id: str
    seller_id: str
    seller_username: str
    buyer_id: str | None
    price: int
    status: Literal["active", "sold", "cancelled"]
    created_at: datetime
    closed_at: datetime | None
    item: ItemInstanceRead

    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def from_model(cls, listing) -> ListingRead:
        return cls(
            id=listing.id,
            seller_id=listing.seller_id,
            seller_username=listing.seller.username,
            buyer_id=listing.buyer_id,
            price=listing.price,
            status=listing.status,
            created_at=listing.created_at,
            closed_at=listing.closed_at,
            item=ItemInstanceRead.model_validate(listing.item),
        )


class ListingFilters(BaseModel):
    slot: ItemSlot | None = None
    rarity: ItemRarity | None = None
