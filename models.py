from pydal import DAL, Field
from datetime import datetime

def model():
    dbinfo = "sqlite://storage.sqlite"
    folder = "./database"

    db = DAL(dbinfo, folder=folder, pool_size=1)
    table(db)
    seed(db)
    return db

def table(db):
    # Usuário
    db.define_table(
        "user",
        Field("name", "string", required=True),
        Field("trade_name", "string"),
        Field("cnpj", "string"),
        Field("address", "string"),
        Field("active", "boolean", default=True),
        Field("email", "string", unique=True),
        Field("password", "password"),  # pyDAL encripta
        Field("created_at", "datetime", default=datetime.now),
        Field("updated_at", "datetime", update=datetime.now),
    )

    # Status
    db.define_table(
        "status",
        Field("name", "string"),
        Field("description", "string"),
        Field("icon", "string"),  # emoji ou ícone CSS
        Field("created_at", "datetime", default=datetime.now),
        Field("updated_at", "datetime", update=datetime.now),
    )

    # Lote (Batch)
    db.define_table(
        "batch",
        Field("code", "string", required=True),
        Field("production_date", "date"),
        Field("quantity", "integer"),
        Field("status", "reference status"),
        Field("owner", "reference user"),
        Field("images", "list:string"),
        Field("details", "json"),
        Field("created_at", "datetime", default=datetime.now),
        Field("updated_at", "datetime", update=datetime.now),
    )

def seed(db):
    seed_status(db)

def seed_status(db):
    statuses = [
        {"name": "Production", "description": "🏭 Production", "icon": "🏭"},
        {"name": "Inspection", "description": "🧪 Inspection", "icon": "🧪"},
        {"name": "Reporting", "description": "📦 Reporting", "icon": "📦"},
        {"name": "Transferred", "description": "↔️ Transferred", "icon": "↔️"},
        {"name": "Shipping", "description": "🚚 Shipping", "icon": "🚚"},
        {"name": "Approved", "description": "🆗 Approved", "icon": "🆗"},
        {"name": "Pending", "description": "🕑 Pending", "icon": "🕑"},
        {"name": "Rejected", "description": "⛔ Rejected", "icon": "⛔"},
        {"name": "Rework", "description": "↩️ Rework", "icon": "↩️"},
        {"name": "Delivered", "description": "✅ Delivered", "icon": "✅"},
    ]

    for status in statuses:
        if not db(db.status.name == status["name"]).count():
            db.status.insert(**status)

    db.commit()