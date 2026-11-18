"""ASGI application: GraphQL endpoint plus the browser console."""
from __future__ import annotations

from .http_app import GraphQLApp

app = GraphQLApp()
