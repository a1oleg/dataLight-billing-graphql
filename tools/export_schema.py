"""Write the GraphQL SDL from the live Strawberry schema to schema.graphql."""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.abspath("."))

from billing.schema import schema  # noqa: E402

output = "schema.graphql"
with open(output, "w", encoding="utf-8", newline="\n") as fh:
    fh.write(schema.as_str())
    fh.write("\n")
print(f"written {output}")
