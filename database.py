from __future__ import annotations

import os
import re
import sqlite3
import unicodedata
from contextlib import contextmanager
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from typing import Iterable

DB_PATH = Path(os.getenv("CHOCOCREN_DB_PATH", "/data/chococren.db"))
PRODUCT_CATEGORIES = ("Trufa", "Barra", "Ovo de Páscoa")
ORDER_STATUSES = ("Em Preparo", "Saiu para Entrega", "Entregue", "Cancelado")
COURIER_STATUSES = ("Disponível", "Em Entrega", "Indisponível", "Em Manutenção")
DEFAULT_MIN_STOCK = 5

