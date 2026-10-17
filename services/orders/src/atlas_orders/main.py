"""ASGI entry point for the orders service."""

from atlas_orders.app.bootstrap import create_app
from atlas_orders.core.config.loader import get_settings

app = create_app(get_settings())
