from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator


class ProductCreate(BaseModel):
    sku: str = Field(min_length=1, max_length=64)
    name: str = Field(min_length=1, max_length=160)
    description: str | None = None
    reorder_level: int = Field(default=0, ge=0)


class ProductUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=160)
    description: str | None = None
    reorder_level: int | None = Field(default=None, ge=0)
    active: bool | None = None


class ProductResponse(ProductCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
    active: bool
    created_at: datetime


class WarehouseCreate(BaseModel):
    name: str = Field(min_length=1, max_length=160)
    location: str | None = Field(default=None, max_length=255)


class WarehouseResponse(WarehouseCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
    active: bool
    created_at: datetime


class StockAdjustmentRequest(BaseModel):
    product_id: int = Field(gt=0)
    warehouse_id: int = Field(gt=0)
    quantity_delta: int
    reason: str | None = Field(default=None, max_length=255)

    @model_validator(mode="after")
    def require_nonzero_quantity(self) -> "StockAdjustmentRequest":
        if self.quantity_delta == 0:
            raise ValueError("quantity_delta cannot be zero")
        return self


class StockTransferRequest(BaseModel):
    product_id: int = Field(gt=0)
    source_warehouse_id: int = Field(gt=0)
    destination_warehouse_id: int = Field(gt=0)
    quantity: int = Field(gt=0)
    reason: str | None = Field(default=None, max_length=255)

    @model_validator(mode="after")
    def distinct_warehouses(self) -> "StockTransferRequest":
        if self.source_warehouse_id == self.destination_warehouse_id:
            raise ValueError("source and destination warehouses must differ")
        return self


class StockResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    product_id: int
    warehouse_id: int
    quantity: int


class StockMovementResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    stock_item_id: int
    movement_type: str
    quantity_delta: int
    reason: str | None
    created_at: datetime
