from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from sqlalchemy import MetaData, Table, create_engine, desc, or_, select, update as sa_update, insert as sa_insert, delete as sa_delete


@dataclass
class QueryResult:
    data: Any


class MySQLClient:
    def __init__(self, url: str):
        self.engine = create_engine(url, pool_pre_ping=True, future=True)
        self.metadata = MetaData()
        self._tables: dict[str, Table] = {}

    def table(self, table_name: str) -> "MySQLTableQuery":
        return MySQLTableQuery(self, table_name)

    def get_table(self, table_name: str) -> Table:
        if table_name not in self._tables:
            self._tables[table_name] = Table(table_name, self.metadata, autoload_with=self.engine)
        return self._tables[table_name]


class MySQLTableQuery:
    def __init__(self, client: MySQLClient, table_name: str):
        self.client = client
        self.table_name = table_name

        self._op: str = "select"
        self._select_columns: str = "*"
        self._payload: dict | list[dict] | None = None
        self._filters: list[tuple[str, Any]] = []
        self._or_filters: list[tuple[str, Any]] = []
        self._order_by: tuple[str, bool] | None = None
        self._offset: int | None = None
        self._limit: int | None = None
        self._single: bool = False

    def select(self, columns: str = "*") -> "MySQLTableQuery":
        self._op = "select"
        self._select_columns = columns or "*"
        return self

    def insert(self, payload: dict | list[dict]) -> "MySQLTableQuery":
        self._op = "insert"
        self._payload = payload
        return self

    def update(self, payload: dict) -> "MySQLTableQuery":
        self._op = "update"
        self._payload = payload
        return self

    def delete(self) -> "MySQLTableQuery":
        self._op = "delete"
        return self

    def eq(self, column: str, value: Any) -> "MySQLTableQuery":
        self._filters.append((column, value))
        return self

    def or_(self, expression: str) -> "MySQLTableQuery":
        # expected format: "col1.eq.val,col2.eq.val"
        for part in (expression or "").split(","):
            part = part.strip()
            if not part or ".eq." not in part:
                continue
            column, value = part.split(".eq.", 1)
            self._or_filters.append((column.strip(), value.strip()))
        return self

    def range(self, start: int, end: int) -> "MySQLTableQuery":
        self._offset = max(0, int(start))
        self._limit = max(0, int(end) - int(start) + 1)
        return self

    def limit(self, n: int) -> "MySQLTableQuery":
        self._limit = int(n)
        return self

    def order(self, column: str, desc: bool = False) -> "MySQLTableQuery":
        self._order_by = (column, bool(desc))
        return self

    def single(self) -> "MySQLTableQuery":
        self._single = True
        self._limit = 1
        return self

    def _apply_filters(self, stmt, table: Table):
        for column, value in self._filters:
            if column in table.c:
                stmt = stmt.where(table.c[column] == value)

        if self._or_filters:
            or_clauses = [table.c[col] == val for col, val in self._or_filters if col in table.c]
            if or_clauses:
                stmt = stmt.where(or_(*or_clauses))

        return stmt

    def _select_stmt(self, table: Table):
        if self._select_columns.strip() == "*":
            stmt = select(table)
        else:
            columns = [c.strip() for c in self._select_columns.split(",") if c.strip()]
            selected = [table.c[c] for c in columns if c in table.c]
            if not selected:
                stmt = select(table)
            else:
                stmt = select(*selected)

        stmt = self._apply_filters(stmt, table)

        if self._order_by and self._order_by[0] in table.c:
            column = table.c[self._order_by[0]]
            stmt = stmt.order_by(desc(column) if self._order_by[1] else column)

        if self._limit is not None:
            stmt = stmt.limit(self._limit)
        if self._offset is not None:
            stmt = stmt.offset(self._offset)

        return stmt

    def execute(self) -> QueryResult:
        table = self.client.get_table(self.table_name)

        with self.client.engine.begin() as conn:
            if self._op == "select":
                stmt = self._select_stmt(table)
                rows = conn.execute(stmt).mappings().all()
                data = [dict(r) for r in rows]
                if self._single:
                    return QueryResult(data=data[0] if data else None)
                return QueryResult(data=data)

            if self._op == "insert":
                payload = self._payload
                if payload is None:
                    return QueryResult(data=[])

                stmt = sa_insert(table)
                if isinstance(payload, list):
                    conn.execute(stmt, payload)
                    return QueryResult(data=payload)

                result = conn.execute(stmt.values(payload))

                primary_keys = [col.name for col in table.primary_key.columns]
                if len(primary_keys) == 1:
                    pk = primary_keys[0]
                    pk_value = payload.get(pk)
                    if pk_value is None and result.inserted_primary_key:
                        pk_value = result.inserted_primary_key[0]
                    if pk_value is not None and pk in table.c:
                        row = conn.execute(select(table).where(table.c[pk] == pk_value)).mappings().first()
                        if row:
                            return QueryResult(data=[dict(row)])

                # Fallback fetch for common unique-key patterns.
                if "email" in table.c and "email" in payload:
                    row = conn.execute(select(table).where(table.c["email"] == payload["email"])).mappings().first()
                    if row:
                        return QueryResult(data=[dict(row)])

                if "student_id" in table.c and "doc_type" in table.c and "student_id" in payload and "doc_type" in payload:
                    row = conn.execute(
                        select(table).where(
                            table.c["student_id"] == payload["student_id"],
                            table.c["doc_type"] == payload["doc_type"],
                        )
                    ).mappings().first()
                    if row:
                        return QueryResult(data=[dict(row)])

                if "aadhaar_card_number" in table.c and "aadhaar_card_number" in payload:
                    row = conn.execute(
                        select(table).where(table.c["aadhaar_card_number"] == payload["aadhaar_card_number"])
                    ).mappings().first()
                    if row:
                        return QueryResult(data=[dict(row)])

                return QueryResult(data=[payload])

            if self._op == "update":
                payload = self._payload or {}
                stmt = sa_update(table).values(payload)
                stmt = self._apply_filters(stmt, table)
                conn.execute(stmt)

                select_stmt = self._select_stmt(table)
                rows = conn.execute(select_stmt).mappings().all()
                return QueryResult(data=[dict(r) for r in rows])

            if self._op == "delete":
                rows_to_delete = conn.execute(self._select_stmt(table)).mappings().all()
                stmt = sa_delete(table)
                stmt = self._apply_filters(stmt, table)
                conn.execute(stmt)
                return QueryResult(data=[dict(r) for r in rows_to_delete])

        return QueryResult(data=[])
