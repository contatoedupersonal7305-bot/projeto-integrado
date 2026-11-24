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


class RuleError(ValueError):
    pass


def now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def normalize_key(value: str) -> str:
    value = unicodedata.normalize("NFKC", str(value or "")).strip().casefold()
    return re.sub(r"\s+", " ", value)


def money_to_cents(value: Decimal | float | int | str) -> int:
    amount = Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    return int(amount * 100)


def cents_to_money(cents: int) -> Decimal:
    return (Decimal(int(cents)) / Decimal(100)).quantize(Decimal("0.01"))


@contextmanager
def connection():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, timeout=20)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA busy_timeout = 20000")
    try:
        yield conn
    finally:
        conn.close()


def initialize_database() -> None:
    with connection() as conn:
        conn.execute("PRAGMA journal_mode = WAL")
        conn.execute("PRAGMA synchronous = NORMAL")
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sku TEXT NOT NULL UNIQUE,
                name TEXT NOT NULL,
                category TEXT NOT NULL CHECK(category IN ('Trufa','Barra','Ovo de Páscoa')),
                flavor TEXT NOT NULL,
                size TEXT NOT NULL,
                category_key TEXT NOT NULL,
                flavor_key TEXT NOT NULL,
                size_key TEXT NOT NULL,
                price_cents INTEGER NOT NULL CHECK(price_cents > 0),
                stock INTEGER NOT NULL DEFAULT 0 CHECK(stock >= 0),
                min_stock INTEGER NOT NULL DEFAULT 5 CHECK(min_stock >= 0),
                active INTEGER NOT NULL DEFAULT 1 CHECK(active IN (0,1)),
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                UNIQUE(category_key, flavor_key, size_key)
            );

            CREATE TABLE IF NOT EXISTS motoboys (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT NOT NULL UNIQUE,
                name TEXT NOT NULL,
                phone TEXT NOT NULL UNIQUE,
                plate TEXT NOT NULL UNIQUE,
                status TEXT NOT NULL CHECK(status IN ('Disponível','Em Entrega','Indisponível','Em Manutenção')),
                active INTEGER NOT NULL DEFAULT 1 CHECK(active IN (0,1)),
                observations TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT NOT NULL UNIQUE,
                customer_name TEXT NOT NULL,
                customer_phone TEXT NOT NULL,
                delivery_address TEXT NOT NULL,
                status TEXT NOT NULL CHECK(status IN ('Em Preparo','Saiu para Entrega','Entregue','Cancelado')),
                motoboy_id INTEGER REFERENCES motoboys(id) ON DELETE RESTRICT,
                subtotal_cents INTEGER NOT NULL CHECK(subtotal_cents >= 0),
                discount_percent TEXT NOT NULL DEFAULT '0',
                discount_cents INTEGER NOT NULL DEFAULT 0 CHECK(discount_cents >= 0),
                delivery_fee_cents INTEGER NOT NULL DEFAULT 0 CHECK(delivery_fee_cents >= 0),
                service_fee_cents INTEGER NOT NULL DEFAULT 0 CHECK(service_fee_cents >= 0),
                total_cents INTEGER NOT NULL CHECK(total_cents >= 0),
                cancellation_reason TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                delivered_at TEXT
            );

            CREATE TABLE IF NOT EXISTS order_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id INTEGER NOT NULL REFERENCES orders(id) ON DELETE RESTRICT,
                product_id INTEGER NOT NULL REFERENCES products(id) ON DELETE RESTRICT,
                product_name TEXT NOT NULL,
                category TEXT NOT NULL,
                flavor TEXT NOT NULL,
                size TEXT NOT NULL,
                quantity INTEGER NOT NULL CHECK(quantity > 0),
                unit_price_cents INTEGER NOT NULL CHECK(unit_price_cents > 0),
                subtotal_cents INTEGER NOT NULL CHECK(subtotal_cents >= 0)
            );

            CREATE TABLE IF NOT EXISTS stock_movements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id INTEGER NOT NULL REFERENCES products(id) ON DELETE CASCADE,
                movement_type TEXT NOT NULL,
                quantity_change INTEGER NOT NULL,
                note TEXT NOT NULL DEFAULT '',
                order_id INTEGER REFERENCES orders(id) ON DELETE SET NULL,
                created_at TEXT NOT NULL
            );

            CREATE INDEX IF NOT EXISTS idx_products_active ON products(active);
            CREATE INDEX IF NOT EXISTS idx_products_stock ON products(stock, min_stock);
            CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status);
            CREATE INDEX IF NOT EXISTS idx_orders_created ON orders(created_at);
            CREATE INDEX IF NOT EXISTS idx_order_items_order ON order_items(order_id);
            CREATE INDEX IF NOT EXISTS idx_stock_movements_product ON stock_movements(product_id);
            """
        )


def _next_code(conn: sqlite3.Connection, table: str, prefix: str) -> str:
    row = conn.execute(f"SELECT COALESCE(MAX(id), 0) + 1 AS next_id FROM {table}").fetchone()
    return f"{prefix}-{int(row['next_id']):05d}"


def _validate_product_fields(
    name: str, category: str, flavor: str, size: str, price_cents: int, stock: int, min_stock: int
) -> None:
    if len(name.strip()) < 2 or len(name.strip()) > 120:
        raise RuleError("O nome do produto deve ter entre 2 e 120 caracteres.")
    if category not in PRODUCT_CATEGORIES:
        raise RuleError("Selecione uma categoria válida: Trufa, Barra ou Ovo de Páscoa.")
    if not flavor.strip() or len(flavor.strip()) > 60:
        raise RuleError("Informe um sabor com até 60 caracteres.")
    size_value = size.strip()
    if len(size_value) > 20 or not re.fullmatch(r"\d+(?:[.,]\d+)?\s?(?:g|kg)", size_value, flags=re.IGNORECASE):
        raise RuleError("Informe um peso válido em gramas ou quilogramas (ex.: 100g ou 1kg).")
    if Decimal(re.match(r"\d+(?:[.,]\d+)?", size_value).group(0).replace(",", ".")) <= 0:
        raise RuleError("O peso do produto deve ser maior que zero.")
    if price_cents <= 0:
        raise RuleError("O preço unitário deve ser maior que zero.")
    if not 0 <= stock <= 1_000_000:
        raise RuleError("O estoque deve estar entre 0 e 1.000.000 unidades.")
    if not 0 <= min_stock <= 1_000_000:
        raise RuleError("O estoque mínimo deve estar entre 0 e 1.000.000 unidades.")


def list_products(include_inactive: bool = True) -> list[dict]:
    with connection() as conn:
        sql = "SELECT * FROM products"
        if not include_inactive:
            sql += " WHERE active = 1"
        sql += " ORDER BY category, flavor, size"
        return [dict(row) for row in conn.execute(sql).fetchall()]


def get_product(product_id: int) -> dict | None:
    with connection() as conn:
        row = conn.execute("SELECT * FROM products WHERE id = ?", (product_id,)).fetchone()
        return dict(row) if row else None


def create_product(
    name: str, category: str, flavor: str, size: str, price_cents: int, stock: int,
    min_stock: int = DEFAULT_MIN_STOCK,
) -> str:
    _validate_product_fields(name, category, flavor, size, price_cents, stock, min_stock)
    timestamp = now_iso()
    try:
        with connection() as conn:
            conn.execute("BEGIN IMMEDIATE")
            code = _next_code(conn, "products", "CH")
            cur = conn.execute(
                """INSERT INTO products
                (sku,name,category,flavor,size,category_key,flavor_key,size_key,price_cents,stock,min_stock,active,created_at,updated_at)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,1,?,?)""",
                (code, name.strip(), category, flavor.strip(), size.strip(), normalize_key(category),
                 normalize_key(flavor), normalize_key(size), price_cents, stock, min_stock, timestamp, timestamp),
            )
            product_id = int(cur.lastrowid)
            if stock:
                conn.execute(
                    "INSERT INTO stock_movements(product_id,movement_type,quantity_change,note,created_at) VALUES(?,?,?,?,?)",
                    (product_id, "ESTOQUE_INICIAL", stock, "Saldo informado no cadastro", timestamp),
                )
            conn.commit()
            return code
    except sqlite3.IntegrityError as exc:
        if "products.category_key" in str(exc) or "UNIQUE constraint failed: products.category_key" in str(exc):
            raise RuleError("Já existe um produto com essa combinação de tipo, sabor e peso.") from exc
        raise RuleError("Não foi possível cadastrar: já existe um SKU ou variação igual.") from exc


def update_product(
    product_id: int, name: str, category: str, flavor: str, size: str, price_cents: int,
    new_stock: int, min_stock: int,
) -> None:
    _validate_product_fields(name, category, flavor, size, price_cents, new_stock, min_stock)
    timestamp = now_iso()
    try:
        with connection() as conn:
            conn.execute("BEGIN IMMEDIATE")
            old = conn.execute("SELECT stock FROM products WHERE id=?", (product_id,)).fetchone()
            if not old:
                raise RuleError("Produto não encontrado.")
            delta = int(new_stock) - int(old["stock"])
            conn.execute(
                """UPDATE products SET name=?,category=?,flavor=?,size=?,category_key=?,flavor_key=?,size_key=?,
                price_cents=?,stock=?,min_stock=?,updated_at=? WHERE id=?""",
                (name.strip(), category, flavor.strip(), size.strip(), normalize_key(category), normalize_key(flavor),
                 normalize_key(size), price_cents, new_stock, min_stock, timestamp, product_id),
            )
            if delta:
                conn.execute(
                    "INSERT INTO stock_movements(product_id,movement_type,quantity_change,note,created_at) VALUES(?,?,?,?,?)",
                    (product_id, "AJUSTE", delta, "Ajuste manual de estoque no cadastro do produto", timestamp),
                )
            conn.commit()
    except sqlite3.IntegrityError as exc:
        raise RuleError("Essa combinação de tipo, sabor e peso já está cadastrada em outro produto.") from exc


def set_product_active(product_id: int, active: bool) -> None:
    with connection() as conn:
        conn.execute("UPDATE products SET active=?,updated_at=? WHERE id=?", (int(active), now_iso(), product_id))


def delete_product_if_unused(product_id: int) -> None:
    with connection() as conn:
        conn.execute("BEGIN IMMEDIATE")
        history = conn.execute("SELECT 1 FROM order_items WHERE product_id=? LIMIT 1", (product_id,)).fetchone()
        if history:
            conn.rollback()
            raise RuleError("Este produto possui histórico de pedidos. Use Inativar em vez de excluir.")
        conn.execute("DELETE FROM products WHERE id=?", (product_id,))
        conn.commit()


def list_motoboys(include_inactive: bool = True) -> list[dict]:
    with connection() as conn:
        sql = "SELECT * FROM motoboys"
        if not include_inactive:
            sql += " WHERE active=1"
        sql += " ORDER BY name COLLATE NOCASE"
        return [dict(row) for row in conn.execute(sql).fetchall()]


def get_motoboy(motoboy_id: int) -> dict | None:
    with connection() as conn:
        row = conn.execute("SELECT * FROM motoboys WHERE id=?", (motoboy_id,)).fetchone()
        return dict(row) if row else None


def create_motoboy(name: str, phone: str, plate: str, status: str, observations: str = "") -> str:
    name, phone, plate = name.strip(), phone.strip(), plate.strip().upper()
    if len(name) < 3 or len(name) > 120:
        raise RuleError("Informe o nome completo do entregador (3 a 120 caracteres).")
    if not re.fullmatch(r"\d{10,11}", phone):
        raise RuleError("Telefone inválido. Informe DDD + número, somente dígitos (10 ou 11 números).")
    if not re.fullmatch(r"[A-Z]{3}\d[A-Z0-9]\d{2}", plate):
        raise RuleError("Placa inválida. Use o padrão ABC1234 ou ABC1D23.")
    if status not in ("Disponível", "Indisponível"):
        raise RuleError("O status inicial deve ser Disponível ou Indisponível.")
    timestamp = now_iso()
    try:
        with connection() as conn:
            conn.execute("BEGIN IMMEDIATE")
            code = _next_code(conn, "motoboys", "MB")
            conn.execute(
                "INSERT INTO motoboys(code,name,phone,plate,status,active,observations,created_at,updated_at) VALUES(?,?,?,?,?,1,?,?,?)",
                (code, name, phone, plate, status, observations.strip(), timestamp, timestamp),
            )
            conn.commit()
            return code
    except sqlite3.IntegrityError as exc:
        raise RuleError("Já existe um entregador com esse telefone ou placa.") from exc


def update_motoboy(
    motoboy_id: int, name: str, phone: str, plate: str, status: str, observations: str = ""
) -> None:
    name, phone, plate = name.strip(), phone.strip(), plate.strip().upper()
    if len(name) < 3 or len(name) > 120:
        raise RuleError("Informe o nome completo do entregador (3 a 120 caracteres).")
    if not re.fullmatch(r"\d{10,11}", phone):
        raise RuleError("Telefone inválido. Informe DDD + número, somente dígitos.")
    if not re.fullmatch(r"[A-Z]{3}\d[A-Z0-9]\d{2}", plate):
        raise RuleError("Placa inválida. Use o padrão ABC1234 ou ABC1D23.")
    if status not in ("Disponível", "Indisponível", "Em Manutenção", "Em Entrega"):
        raise RuleError("Status de entregador inválido.")
    with connection() as conn:
        conn.execute("BEGIN IMMEDIATE")
        current = conn.execute("SELECT status FROM motoboys WHERE id=?", (motoboy_id,)).fetchone()
        if not current:
            conn.rollback()
            raise RuleError("Entregador não encontrado.")
        active_route = conn.execute(
            "SELECT 1 FROM orders WHERE motoboy_id=? AND status='Saiu para Entrega' LIMIT 1", (motoboy_id,)
        ).fetchone()
        if active_route and status != "Em Entrega":
            conn.rollback()
            raise RuleError("Este entregador possui uma entrega em rota. Finalize ou cancele o pedido antes de alterar o status.")
        if current["status"] == "Em Entrega" and not active_route and status == "Em Entrega":
            pass
        try:
            conn.execute(
                "UPDATE motoboys SET name=?,phone=?,plate=?,status=?,observations=?,updated_at=? WHERE id=?",
                (name, phone, plate, status, observations.strip(), now_iso(), motoboy_id),
            )
            conn.commit()
        except sqlite3.IntegrityError as exc:
            conn.rollback()
            raise RuleError("Já existe outro entregador com esse telefone ou placa.") from exc


def set_motoboy_active(motoboy_id: int, active: bool) -> None:
    with connection() as conn:
        conn.execute("BEGIN IMMEDIATE")
        active_route = conn.execute(
            "SELECT 1 FROM orders WHERE motoboy_id=? AND status='Saiu para Entrega' LIMIT 1", (motoboy_id,)
        ).fetchone()
        if active_route and not active:
            conn.rollback()
            raise RuleError("Não é possível inativar um entregador com entrega em rota.")
        conn.execute("UPDATE motoboys SET active=?,updated_at=? WHERE id=?", (int(active), now_iso(), motoboy_id))
        conn.commit()


def delete_motoboy_if_unused(motoboy_id: int) -> None:
    with connection() as conn:
        conn.execute("BEGIN IMMEDIATE")
        history = conn.execute("SELECT 1 FROM orders WHERE motoboy_id=? LIMIT 1", (motoboy_id,)).fetchone()
        if history:
            conn.rollback()
            raise RuleError("Este entregador possui histórico de pedidos. Use Inativar em vez de excluir.")
        conn.execute("DELETE FROM motoboys WHERE id=?", (motoboy_id,))
        conn.commit()


def available_motoboys() -> list[dict]:
    with connection() as conn:
        return [dict(r) for r in conn.execute(
            "SELECT * FROM motoboys WHERE active=1 AND status='Disponível' ORDER BY name COLLATE NOCASE"
        ).fetchall()]


def create_order(
    customer_name: str,
    customer_phone: str,
    delivery_address: str,
    items: Iterable[tuple[int, int]],
    discount_percent: Decimal,
    delivery_fee_cents: int,
    service_fee_cents: int,
) -> str:
    customer_name = customer_name.strip()
    customer_phone = customer_phone.strip()
    delivery_address = delivery_address.strip()
    if len(customer_name) < 2 or len(customer_name) > 120:
        raise RuleError("Informe o nome do cliente (2 a 120 caracteres).")
    if not re.fullmatch(r"\d{10,11}", customer_phone):
        raise RuleError("Telefone inválido. Informe DDD + número, somente dígitos (10 ou 11 números).")
    if len(delivery_address) < 8 or len(delivery_address) > 250:
        raise RuleError("Informe um endereço de entrega completo (8 a 250 caracteres).")
    if not Decimal("0") <= discount_percent <= Decimal("100"):
        raise RuleError("O desconto deve estar entre 0% e 100%.")
    if delivery_fee_cents < 0 or service_fee_cents < 0:
        raise RuleError("Taxas não podem ter valores negativos.")

    quantities: dict[int, int] = {}
    for product_id, quantity in items:
        product_id, quantity = int(product_id), int(quantity)
        if quantity <= 0 or quantity > 1_000:
            raise RuleError("A quantidade de cada produto deve ser de 1 a 1.000 unidades.")
        quantities[product_id] = quantities.get(product_id, 0) + quantity
    if not quantities:
        raise RuleError("Adicione pelo menos um produto ao pedido.")

    timestamp = now_iso()
    with connection() as conn:
        conn.execute("BEGIN IMMEDIATE")
        product_rows = {}
        subtotal = 0
        for product_id, quantity in quantities.items():
            row = conn.execute("SELECT * FROM products WHERE id=?", (product_id,)).fetchone()
            if not row or not row["active"]:
                conn.rollback()
                raise RuleError("Um dos produtos do carrinho foi inativado. Atualize o carrinho e tente novamente.")
            if row["stock"] < quantity:
                conn.rollback()
                raise RuleError(f"Estoque insuficiente para {row['name']}. Disponível: {row['stock']}; solicitado: {quantity}.")
            product_rows[product_id] = row
            subtotal += int(row["price_cents"]) * quantity

        discount_cents = int(
            (Decimal(subtotal) * discount_percent / Decimal(100)).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
        )
        total = subtotal - discount_cents + delivery_fee_cents + service_fee_cents
        next_id = int(conn.execute("SELECT COALESCE(MAX(id),0)+1 FROM orders").fetchone()[0])
        order_code = f"#{next_id:05d}"
        cur = conn.execute(
            """INSERT INTO orders(code,customer_name,customer_phone,delivery_address,status,subtotal_cents,
            discount_percent,discount_cents,delivery_fee_cents,service_fee_cents,total_cents,created_at,updated_at)
            VALUES(?,?,?,?,'Em Preparo',?,?,?,?,?,?,?,?)""",
            (order_code, customer_name, customer_phone, delivery_address, subtotal, str(discount_percent),
             discount_cents, delivery_fee_cents, service_fee_cents, total, timestamp, timestamp),
        )
        order_id = int(cur.lastrowid)
        for product_id, quantity in quantities.items():
            product = product_rows[product_id]
            updated = conn.execute(
                "UPDATE products SET stock=stock-?,updated_at=? WHERE id=? AND active=1 AND stock>=?",
                (quantity, timestamp, product_id, quantity),
            )
            if updated.rowcount != 1:
                conn.rollback()
                raise RuleError(f"O estoque de {product['name']} mudou. Atualize o pedido e tente novamente.")
            line_total = int(product["price_cents"]) * quantity
            conn.execute(
                """INSERT INTO order_items(order_id,product_id,product_name,category,flavor,size,quantity,unit_price_cents,subtotal_cents)
                VALUES(?,?,?,?,?,?,?,?,?)""",
                (order_id, product_id, product["name"], product["category"], product["flavor"], product["size"],
                 quantity, product["price_cents"], line_total),
            )
            conn.execute(
                "INSERT INTO stock_movements(product_id,movement_type,quantity_change,note,order_id,created_at) VALUES(?,?,?,?,?,?)",
                (product_id, "SAIDA_VENDA", -quantity, f"Baixa pelo pedido {order_code}", order_id, timestamp),
            )
        conn.commit()
        return order_code


def list_orders(status: str = "Todos", search: str = "", limit: int = 200) -> list[dict]:
    sql = """SELECT o.*, m.name AS motoboy_name, m.code AS motoboy_code
             FROM orders o LEFT JOIN motoboys m ON m.id=o.motoboy_id WHERE 1=1"""
    params: list = []
    if status != "Todos":
        sql += " AND o.status=?"
        params.append(status)
    if search.strip():
        term = f"%{search.strip()}%"
        sql += " AND (o.code LIKE ? OR o.customer_name LIKE ? OR EXISTS (SELECT 1 FROM order_items oi WHERE oi.order_id=o.id AND oi.product_name LIKE ?))"
        params.extend((term, term, term))
    sql += " ORDER BY o.id DESC LIMIT ?"
    params.append(int(limit))
    with connection() as conn:
        return [dict(r) for r in conn.execute(sql, params).fetchall()]


def get_order(order_id: int) -> dict | None:
    with connection() as conn:
        order = conn.execute(
            "SELECT o.*,m.name AS motoboy_name,m.code AS motoboy_code FROM orders o LEFT JOIN motoboys m ON m.id=o.motoboy_id WHERE o.id=?",
            (order_id,),
        ).fetchone()
        if not order:
            return None
        result = dict(order)
        result["items"] = [dict(r) for r in conn.execute("SELECT * FROM order_items WHERE order_id=?", (order_id,)).fetchall()]
        return result


def assign_order_to_motoboy(order_id: int, motoboy_id: int) -> None:
    timestamp = now_iso()
    with connection() as conn:
        conn.execute("BEGIN IMMEDIATE")
        order = conn.execute("SELECT status FROM orders WHERE id=?", (order_id,)).fetchone()
        courier = conn.execute("SELECT status,active FROM motoboys WHERE id=?", (motoboy_id,)).fetchone()
        if not order or order["status"] != "Em Preparo":
            conn.rollback()
            raise RuleError("Somente pedidos Em Preparo podem ser despachados.")
        if not courier or not courier["active"] or courier["status"] != "Disponível":
            conn.rollback()
            raise RuleError("O entregador selecionado não está disponível.")
        conn.execute("UPDATE orders SET status='Saiu para Entrega',motoboy_id=?,updated_at=? WHERE id=?", (motoboy_id, timestamp, order_id))
        conn.execute("UPDATE motoboys SET status='Em Entrega',updated_at=? WHERE id=?", (timestamp, motoboy_id))
        conn.commit()


def complete_delivery(order_id: int) -> None:
    timestamp = now_iso()
    with connection() as conn:
        conn.execute("BEGIN IMMEDIATE")
        order = conn.execute("SELECT status,motoboy_id FROM orders WHERE id=?", (order_id,)).fetchone()
        if not order or order["status"] != "Saiu para Entrega":
            conn.rollback()
            raise RuleError("Somente pedidos que saíram para entrega podem ser concluídos.")
        conn.execute("UPDATE orders SET status='Entregue',delivered_at=?,updated_at=? WHERE id=?", (timestamp, timestamp, order_id))
        if order["motoboy_id"] is not None:
            other = conn.execute(
                "SELECT 1 FROM orders WHERE motoboy_id=? AND status='Saiu para Entrega' AND id<>? LIMIT 1",
                (order["motoboy_id"], order_id),
            ).fetchone()
            if not other:
                conn.execute("UPDATE motoboys SET status='Disponível',updated_at=? WHERE id=? AND active=1", (timestamp, order["motoboy_id"]))
        conn.commit()


def cancel_order(order_id: int, reason: str) -> None:
    reason = reason.strip()
    if len(reason) < 5 or len(reason) > 500:
        raise RuleError("Descreva o motivo do cancelamento (5 a 500 caracteres).")
    timestamp = now_iso()
    with connection() as conn:
        conn.execute("BEGIN IMMEDIATE")
        order = conn.execute("SELECT status,motoboy_id,code FROM orders WHERE id=?", (order_id,)).fetchone()
        if not order or order["status"] not in ("Em Preparo", "Saiu para Entrega"):
            conn.rollback()
            raise RuleError("Este pedido não pode mais ser cancelado. Pedidos Entregues ou já Cancelados não permitem estorno.")
        items = conn.execute("SELECT product_id,quantity FROM order_items WHERE order_id=?", (order_id,)).fetchall()
        for item in items:
            conn.execute("UPDATE products SET stock=stock+?,updated_at=? WHERE id=?", (item["quantity"], timestamp, item["product_id"]))
            conn.execute(
                "INSERT INTO stock_movements(product_id,movement_type,quantity_change,note,order_id,created_at) VALUES(?,?,?,?,?,?)",
                (item["product_id"], "ESTORNO_CANCELAMENTO", item["quantity"], f"Estorno do pedido {order['code']}", order_id, timestamp),
            )
        conn.execute(
            "UPDATE orders SET status='Cancelado',cancellation_reason=?,updated_at=? WHERE id=?",
            (reason, timestamp, order_id),
        )
        if order["motoboy_id"] is not None:
            other = conn.execute(
                "SELECT 1 FROM orders WHERE motoboy_id=? AND status='Saiu para Entrega' AND id<>? LIMIT 1",
                (order["motoboy_id"], order_id),
            ).fetchone()
            if not other:
                conn.execute(
                    "UPDATE motoboys SET status='Disponível',updated_at=? WHERE id=? AND active=1 AND status='Em Entrega'",
                    (timestamp, order["motoboy_id"]),
                )
        conn.commit()


def dashboard_metrics() -> dict:
    with connection() as conn:
        def scalar(sql: str, params: tuple = ()) -> int:
            return int(conn.execute(sql, params).fetchone()[0] or 0)
        return {
            "orders_preparing": scalar("SELECT COUNT(*) FROM orders WHERE status='Em Preparo'"),
            "orders_route": scalar("SELECT COUNT(*) FROM orders WHERE status='Saiu para Entrega'"),
            "couriers_available": scalar("SELECT COUNT(*) FROM motoboys WHERE active=1 AND status='Disponível'"),
            "products_low": scalar("SELECT COUNT(*) FROM products WHERE active=1 AND stock<min_stock"),
            "products_total": scalar("SELECT COUNT(*) FROM products WHERE active=1"),
            "couriers_total": scalar("SELECT COUNT(*) FROM motoboys WHERE active=1"),
        }


def low_stock_products() -> list[dict]:
    with connection() as conn:
        return [dict(r) for r in conn.execute(
            "SELECT * FROM products WHERE active=1 AND stock<min_stock ORDER BY stock ASC, name COLLATE NOCASE"
        ).fetchall()]


def monthly_order_summary(month_count: int = 11) -> list[dict]:
    now = datetime.now()
    months = []
    year, month = now.year, now.month
    for _ in range(month_count - 1, -1, -1):
        y, m = year, month - _
        while m <= 0:
            m += 12
            y -= 1
        months.append((f"{y:04d}-{m:02d}", f"{m:02d}/{str(y)[-2:]}"))
    with connection() as conn:
        rows = conn.execute(
            "SELECT substr(created_at,1,7) AS ym, SUM(total_cents) AS total FROM orders WHERE status<>'Cancelado' GROUP BY substr(created_at,1,7)"
        ).fetchall()
    values = {r["ym"]: int(r["total"] or 0) for r in rows}
    return [{"Mês": label, "Valor dos pedidos (R$)": round(values.get(key, 0) / 100, 2)} for key, label in months]


def get_stock_movements(product_id: int, limit: int = 30) -> list[dict]:
    with connection() as conn:
        return [dict(r) for r in conn.execute(
            "SELECT * FROM stock_movements WHERE product_id=? ORDER BY id DESC LIMIT ?", (product_id, limit)
        ).fetchall()]


def product_has_order_history(product_id: int) -> bool:
    with connection() as conn:
        return conn.execute("SELECT 1 FROM order_items WHERE product_id=? LIMIT 1", (product_id,)).fetchone() is not None


def motoboy_has_order_history(motoboy_id: int) -> bool:
    with connection() as conn:
        return conn.execute("SELECT 1 FROM orders WHERE motoboy_id=? LIMIT 1", (motoboy_id,)).fetchone() is not None
