"""
validators.py
-------------
All input validation logic lives here, keeping the CLI and order layers clean.
Raises ValidationError with user-friendly messages on any invalid input.
"""

import logging
from typing import Optional, Tuple

logger = logging.getLogger(__name__)

VALID_SIDES = {"BUY", "SELL"}
VALID_ORDER_TYPES = {"MARKET", "LIMIT"}
MIN_QUANTITY = 0.001


class ValidationError(Exception):
    """Raised when user-supplied input fails validation."""
    pass


def validate_symbol(symbol: str) -> str:
    """
    Validate and normalize the trading symbol.
    Must be a non-empty alphabetic string (e.g. BTCUSDT).
    """
    symbol = symbol.strip().upper()
    if not symbol:
        raise ValidationError("Symbol cannot be empty. Example: BTCUSDT")
    if not symbol.isalpha():
        raise ValidationError(
            f"Symbol '{symbol}' must contain letters only (no numbers/spaces). "
            "Example: BTCUSDT, ETHUSDT"
        )
    if len(symbol) < 5:
        raise ValidationError(
            f"Symbol '{symbol}' looks too short. Expected format: BTCUSDT"
        )
    logger.debug(f"Symbol validated: {symbol}")
    return symbol


def validate_side(side: str) -> str:
    """Validate order side — must be BUY or SELL."""
    side = side.strip().upper()
    if side not in VALID_SIDES:
        raise ValidationError(
            f"Invalid side '{side}'. Must be one of: {', '.join(sorted(VALID_SIDES))}"
        )
    logger.debug(f"Side validated: {side}")
    return side


def validate_order_type(order_type: str) -> str:
    """Validate order type — must be MARKET or LIMIT."""
    order_type = order_type.strip().upper()
    if order_type not in VALID_ORDER_TYPES:
        raise ValidationError(
            f"Invalid order type '{order_type}'. "
            f"Must be one of: {', '.join(sorted(VALID_ORDER_TYPES))}"
        )
    logger.debug(f"Order type validated: {order_type}")
    return order_type


def validate_quantity(quantity) -> float:
    """
    Validate order quantity.
    Must be a positive number >= MIN_QUANTITY.
    """
    try:
        qty = float(quantity)
    except (ValueError, TypeError):
        raise ValidationError(
            f"Invalid quantity '{quantity}'. Must be a positive number. Example: 0.01"
        )
    if qty <= 0:
        raise ValidationError(
            f"Quantity must be greater than 0. Got: {qty}"
        )
    if qty < MIN_QUANTITY:
        raise ValidationError(
            f"Quantity {qty} is below the minimum allowed ({MIN_QUANTITY})."
        )
    logger.debug(f"Quantity validated: {qty}")
    return round(qty, 8)


def validate_price(price, order_type: str) -> Optional[float]:
    """
    Validate order price.
    - Required for LIMIT orders.
    - Must be a positive number.
    - Ignored (returns None) for MARKET orders.
    """
    if order_type == "LIMIT":
        if price is None or str(price).strip() == "":
            raise ValidationError(
                "Price is required for LIMIT orders. Example: --price 65000.50"
            )
        try:
            p = float(price)
        except (ValueError, TypeError):
            raise ValidationError(
                f"Invalid price '{price}'. Must be a positive number. Example: 65000.50"
            )
        if p <= 0:
            raise ValidationError(
                f"Price must be greater than 0. Got: {p}"
            )
        logger.debug(f"Price validated: {p}")
        return round(p, 8)

    # For MARKET orders, price is not used
    if price is not None and str(price).strip() != "":
        logger.warning(
            f"Price '{price}' was provided but will be ignored for MARKET orders."
        )
    return None


def validate_all(
    symbol: str,
    side: str,
    order_type: str,
    quantity,
    price=None,
) -> Tuple[str, str, str, float, Optional[float]]:
    """
    Run all validations and return clean, normalized values.

    Returns:
        Tuple of (symbol, side, order_type, quantity, price)
    """
    sym = validate_symbol(symbol)
    sd = validate_side(side)
    ot = validate_order_type(order_type)
    qty = validate_quantity(quantity)
    prc = validate_price(price, ot)

    logger.info(
        f"Validation passed → symbol={sym}, side={sd}, "
        f"type={ot}, qty={qty}, price={prc}"
    )
    return sym, sd, ot, qty, prc
