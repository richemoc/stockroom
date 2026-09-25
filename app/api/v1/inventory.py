from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.models import Product, StockItem, StockMovement
from app.schemas.inventory import (
    StockAdjustmentRequest,
    StockMovementResponse,
    StockResponse,
    StockTransferRequest,
)
from app.services.inventory_service import InventoryError, adjust_stock, transfer_stock

router = APIRouter()


def _stock_response(stock: StockItem) -> StockResponse:
    return StockResponse(
        product_id=stock.product_id,
        warehouse_id=stock.warehouse_id,
        quantity=stock.quantity,
    )


@router.get("", response_model=list[StockResponse])
def list_inventory(
    product_id: int | None = Query(default=None, gt=0),
    warehouse_id: int | None = Query(default=None, gt=0),
    db: Session = Depends(get_db),
) -> list[StockResponse]:
    query = select(StockItem).order_by(StockItem.product_id, StockItem.warehouse_id)
    if product_id:
        query = query.where(StockItem.product_id == product_id)
    if warehouse_id:
        query = query.where(StockItem.warehouse_id == warehouse_id)
    return [_stock_response(stock) for stock in db.scalars(query).all()]


@router.get("/low-stock", response_model=list[StockResponse])
def list_low_stock(db: Session = Depends(get_db)) -> list[StockResponse]:
    query = (
        select(StockItem)
        .join(Product)
        .where(StockItem.quantity <= Product.reorder_level)
        .order_by(StockItem.quantity)
    )
    return [_stock_response(stock) for stock in db.scalars(query).all()]


@router.post("/adjustments", response_model=StockResponse)
def create_adjustment(payload: StockAdjustmentRequest, db: Session = Depends(get_db)) -> StockResponse:
    try:
        stock = adjust_stock(db, **payload.model_dump())
    except InventoryError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return _stock_response(stock)


@router.post("/transfers", response_model=list[StockResponse])
def create_transfer(payload: StockTransferRequest, db: Session = Depends(get_db)) -> list[StockResponse]:
    try:
        source, destination = transfer_stock(db, **payload.model_dump())
    except InventoryError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return [_stock_response(source), _stock_response(destination)]


@router.get("/history", response_model=list[StockMovementResponse])
def inventory_history(
    product_id: int | None = Query(default=None, gt=0),
    warehouse_id: int | None = Query(default=None, gt=0),
    db: Session = Depends(get_db),
) -> list[StockMovementResponse]:
    query = select(StockMovement).join(StockItem).order_by(StockMovement.id.desc())
    if product_id:
        query = query.where(StockItem.product_id == product_id)
    if warehouse_id:
        query = query.where(StockItem.warehouse_id == warehouse_id)
    return list(db.scalars(query).all())
