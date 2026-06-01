"""
orders.py
---------
Business logic for placing futures orders.
Translates validated user inputs into Binance API calls via BinanceClient.
"""

import logging
from typing import Any, Dict, Optional

from .client import BinanceClient

logger = logging.getLogger(__name__)


class OrderManager:
    """
    Manages order placement on Binance Futures Testnet.

    Wraps BinanceClient with order-type-specific logic and
    ensures all required parameters are correctly assembled.
    """

    def __init__(self, client: BinanceClient):
        self.client = client

    # ------------------------------------------------------------------ #
    #  Order types                                                         #
    # ------------------------------------------------------------------ #

    def place_market_order(
        self, symbol: str, side: str, quantity: float
    ) -> Dict[str, Any]:
        """
        Place a MARKET order — executes immediately at the best available price.

        Args:
            symbol:   Trading pair, e.g. 'BTCUSDT'
            side:     'BUY' or 'SELL'
            quantity: Amount to trade

        Returns:
            Raw order response from the Binance API.
        """
        logger.info(
            f"Placing MARKET order → {side} {quantity} {symbol}"
        )
        return self.client.place_order(
            symbol=symbol,
            side=side,
            type="MARKET",
            quantity=quantity,
        )

    def place_limit_order(
        self, symbol: str, side: str, quantity: float, price: float
    ) -> Dict[str, Any]:
        """
        Place a LIMIT order — rests in the order book until filled at `price`.

        Args:
            symbol:   Trading pair, e.g. 'BTCUSDT'
            side:     'BUY' or 'SELL'
            quantity: Amount to trade
            price:    Limit price

        Returns:
            Raw order response from the Binance API.
        """
        logger.info(
            f"Placing LIMIT order → {side} {quantity} {symbol} @ {price}"
        )
        return self.client.place_order(
            symbol=symbol,
            side=side,
            type="LIMIT",
            quantity=quantity,
            price=price,
            timeInForce="GTC",   # Good Till Cancelled
        )

    # ------------------------------------------------------------------ #
    #  Unified entry point                                                 #
    # ------------------------------------------------------------------ #

    def place_order(
        self,
        symbol: str,
        side: str,
        order_type: str,
        quantity: float,
        price: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Unified order placement — dispatches to the correct method.

        Args:
            symbol:     Trading pair
            side:       'BUY' or 'SELL'
            order_type: 'MARKET' or 'LIMIT'
            quantity:   Amount to trade
            price:      Required for LIMIT; ignored for MARKET

        Returns:
            Raw order response from the Binance API.

        Raises:
            ValueError: If order_type is unsupported.
        """
        if order_type == "MARKET":
            return self.place_market_order(symbol, side, quantity)
        elif order_type == "LIMIT":
            if price is None:
                raise ValueError("Price is required for LIMIT orders.")
            return self.place_limit_order(symbol, side, quantity, price)
        else:
            raise ValueError(
                f"Unsupported order type: '{order_type}'. "
                "Expected 'MARKET' or 'LIMIT'."
            )
