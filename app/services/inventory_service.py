from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Product, StockItem, StockMovement, Warehouse


class InventoryError(Exception):
    pass


def _get_product_and_warehouse(db: Session, product_id: int, warehouse_id: int) -> None:
    if db.get(Product, product_id) is None:
        raise InventoryError("Product not found")
    if db.get(Warehouse, warehouse_id) is None:
        raise InventoryError("Warehouse not found")


def _get_or_create_stock(
    db: Session, product_id: int, warehouse_id: int, *, create: bool = True
) -> StockItem:
    stock = db.scalar(
        select(StockItem)
        .where(StockItem.product_id == product_id, StockItem.warehouse_id == warehouse_id)
        .with_for_update()
    )
    if stock is None and create:
        stock = StockItem(product_id=product_id, warehouse_id=warehouse_id, quantity=0)
        db.add(stock)
        db.flush()
    if stock is None:
        raise InventoryError("Stock record not found")
    return stock


def adjust_stock(
    db: Session, product_id: int, warehouse_id: int, quantity_delta: int, reason: str | None
) -> StockItem:
    _get_product_and_warehouse(db, product_id, warehouse_id)
    stock = _get_or_create_stock(db, product_id, warehouse_id)
    new_quantity = stock.quantity + quantity_delta
    if new_quantity < 0:
        raise InventoryError("Adjustment would make stock negative")
    stock.quantity = new_quantity
    db.add(
        StockMovement(
            stock_item_id=stock.id,
            movement_type="ADJUSTMENT",
            quantity_delta=quantity_delta,
            reason=reason,
        )
    )
    db.commit()
    db.refresh(stock)
    return stock


def transfer_stock(
    db: Session,
    product_id: int,
    source_warehouse_id: int,
    destination_warehouse_id: int,
    quantity: int,
    reason: str | None,
) -> tuple[StockItem, StockItem]:
    _get_product_and_warehouse(db, product_id, source_warehouse_id)
    _get_product_and_warehouse(db, product_id, destination_warehouse_id)
    source = _get_or_create_stock(db, product_id, source_warehouse_id, create=False)
    destination = _get_or_create_stock(db, product_id, destination_warehouse_id)
    if source.quantity < quantity:
        raise InventoryError("Transfer would make source stock negative")
    source.quantity -= quantity
    destination.quantity += quantity
    db.add_all(
        [
            StockMovement(
                stock_item_id=source.id,
                movement_type="TRANSFER_OUT",
                quantity_delta=-quantity,
                reason=reason,
            ),
            StockMovement(
                stock_item_id=destination.id,
                movement_type="TRANSFER_IN",
                quantity_delta=quantity,
                reason=reason,
            ),
        ]
    )
    db.commit()
    db.refresh(source)
    db.refresh(destination)
    return source, destination
