from __future__ import annotations

import hashlib
import threading
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd
from flask import Flask, jsonify, redirect, request, send_from_directory
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestRegressor
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder


BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent
DATA_PATH = BASE_DIR / "data" / "crop_history.csv"
TRACE_DB_PATH = BASE_DIR / "data" / "produce_traceability.sqlite3"
IOT_DB_PATH = BASE_DIR / "data" / "iot_telemetry.sqlite3"
IOT_DEFAULT_THRESHOLD = 32.0
IOT_WORKER_INTERVAL_SECONDS = 60

PRICE_PER_TON = {
    "Corn": 320,
    "Wheat": 400,
    "Rice": 460,
    "Soybean": 520,
    "Cotton": 610,
}

app = Flask(__name__)


@app.after_request
def add_cors_headers(response):
    response.headers.setdefault("Access-Control-Allow-Origin", "*")
    response.headers.setdefault("Access-Control-Allow-Headers", "Content-Type")
    response.headers.setdefault("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
    return response

FARMERS = [
    (1, "Asha Patel", "Modasa, Gujarat"),
    (2, "Rahul Verma", "Karnal, Haryana"),
    (3, "Meera Nair", "Erode, Tamil Nadu"),
]

CROPS = [
    (1, "Corn", "Sweet Gold"),
    (2, "Wheat", "Durum"),
    (3, "Rice", "Jaya"),
]

BATCH_SEEDS = [
    {
        "id": 101,
        "batch_code": "BATCH-101-ALPHA",
        "farmer_id": 1,
        "crop_id": 1,
        "planting_date": "2026-01-12",
        "harvest_date": "2026-05-04",
        "fertilizer_summary": "Compost, NPK 10-26-26, seaweed extract",
        "acreage": 12.5,
        "batch_notes": "North field block A",
    },
    {
        "id": 102,
        "batch_code": "BATCH-102-BRAVO",
        "farmer_id": 2,
        "crop_id": 2,
        "planting_date": "2026-01-18",
        "harvest_date": "2026-05-16",
        "fertilizer_summary": "Farmyard manure, urea, potassium sulfate",
        "acreage": 18.0,
        "batch_notes": "River belt parcel 7",
    },
    {
        "id": 103,
        "batch_code": "BATCH-103-CHARLIE",
        "farmer_id": 3,
        "crop_id": 3,
        "planting_date": "2026-02-02",
        "harvest_date": "2026-06-01",
        "fertilizer_summary": "Vermicompost, DAP, micronutrient spray",
        "acreage": 20.0,
        "batch_notes": "Lowland paddy zone",
    },
]

LEDGER_EVENTS = [
    ("Planted", 0, "Seeds placed and irrigation activated."),
    ("Fertilized", 18, "Primary fertilizer treatment completed."),
    ("Harvested", 112, "Crop harvested and quality inspected."),
    ("Shipped", 118, "Sealed batch shipped to distribution center."),
]

IOT_SEEDS = [
    {
        "device_id": "ESP32-NORTH-01",
        "farmer_name": "Asha Patel",
        "farm_name": "North Field",
        "soil_moisture": 41.5,
        "temperature": 29.8,
        "humidity": 56.2,
        "nitrogen": 21.0,
        "phosphorus": 18.0,
        "potassium": 24.0,
        "moisture_threshold": 32.0,
        "sample_offset_minutes": 240,
    },
    {
        "device_id": "ESP32-NORTH-01",
        "farmer_name": "Asha Patel",
        "farm_name": "North Field",
        "soil_moisture": 36.8,
        "temperature": 30.4,
        "humidity": 53.5,
        "nitrogen": 20.2,
        "phosphorus": 17.6,
        "potassium": 23.4,
        "moisture_threshold": 32.0,
        "sample_offset_minutes": 180,
    },
    {
        "device_id": "ESP32-NORTH-01",
        "farmer_name": "Asha Patel",
        "farm_name": "North Field",
        "soil_moisture": 28.9,
        "temperature": 31.7,
        "humidity": 48.9,
        "nitrogen": 19.5,
        "phosphorus": 16.8,
        "potassium": 22.1,
        "moisture_threshold": 32.0,
        "sample_offset_minutes": 120,
    },
    {
        "device_id": "ESP32-SOUTH-07",
        "farmer_name": "Rahul Verma",
        "farm_name": "South Orchard",
        "soil_moisture": 45.7,
        "temperature": 27.9,
        "humidity": 61.8,
        "nitrogen": 22.4,
        "phosphorus": 19.0,
        "potassium": 25.7,
        "moisture_threshold": 30.0,
        "sample_offset_minutes": 210,
    },
    {
        "device_id": "ESP32-SOUTH-07",
        "farmer_name": "Rahul Verma",
        "farm_name": "South Orchard",
        "soil_moisture": 39.3,
        "temperature": 28.6,
        "humidity": 58.0,
        "nitrogen": 21.8,
        "phosphorus": 18.8,
        "potassium": 24.9,
        "moisture_threshold": 30.0,
        "sample_offset_minutes": 150,
    },
    {
        "device_id": "ESP32-SOUTH-07",
        "farmer_name": "Rahul Verma",
        "farm_name": "South Orchard",
        "soil_moisture": 27.4,
        "temperature": 30.1,
        "humidity": 51.1,
        "nitrogen": 18.9,
        "phosphorus": 16.7,
        "potassium": 21.6,
        "moisture_threshold": 30.0,
        "sample_offset_minutes": 60,
    },
]


def load_model() -> Pipeline:
    data = pd.read_csv(DATA_PATH)
    features = ["acreage", "seed_cost", "fertilizer_cost", "budget", "soil_type", "target_crop"]
    target = "historical_yield_tons"

    preprocessor = ColumnTransformer(
        transformers=[
            (
                "categorical",
                OneHotEncoder(handle_unknown="ignore", sparse_output=False),
                ["soil_type", "target_crop"],
            ),
        ],
        remainder="passthrough",
    )

    model = RandomForestRegressor(n_estimators=200, random_state=42)
    pipeline = Pipeline([
        ("preprocessor", preprocessor),
        ("model", model),
    ])
    pipeline.fit(data[features], data[target])
    return pipeline


MODEL = load_model()


def get_traceability_connection() -> sqlite3.Connection:
    connection = sqlite3.connect(TRACE_DB_PATH)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def get_iot_connection() -> sqlite3.Connection:
    connection = sqlite3.connect(IOT_DB_PATH)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def compute_event_hash(batch_id: int, event_type: str, event_date: str, details: str, previous_hash: str) -> str:
    payload = f"{batch_id}|{event_type}|{event_date}|{details}|{previous_hash}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def ensure_traceability_db() -> None:
    TRACE_DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    with get_traceability_connection() as connection:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS farmers (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                location TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS crops (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                variety TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS batches (
                id INTEGER PRIMARY KEY,
                batch_code TEXT NOT NULL UNIQUE,
                farmer_id INTEGER NOT NULL,
                crop_id INTEGER NOT NULL,
                planting_date TEXT NOT NULL,
                harvest_date TEXT NOT NULL,
                fertilizer_summary TEXT NOT NULL,
                acreage REAL NOT NULL,
                batch_notes TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY (farmer_id) REFERENCES farmers(id),
                FOREIGN KEY (crop_id) REFERENCES crops(id)
            );

            CREATE TABLE IF NOT EXISTS ledger_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                batch_id INTEGER NOT NULL,
                event_type TEXT NOT NULL,
                event_date TEXT NOT NULL,
                details TEXT NOT NULL,
                previous_hash TEXT NOT NULL,
                event_hash TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (batch_id) REFERENCES batches(id)
            );
            """
        )

        if connection.execute("SELECT COUNT(*) FROM batches").fetchone()[0]:
            return

        connection.executemany("INSERT INTO farmers (id, name, location) VALUES (?, ?, ?)", FARMERS)
        connection.executemany("INSERT INTO crops (id, name, variety) VALUES (?, ?, ?)", CROPS)

        for batch in BATCH_SEEDS:
            created_at = datetime.utcnow().isoformat(timespec="seconds") + "Z"
            connection.execute(
                """
                INSERT INTO batches (
                    id, batch_code, farmer_id, crop_id, planting_date, harvest_date,
                    fertilizer_summary, acreage, batch_notes, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    batch["id"],
                    batch["batch_code"],
                    batch["farmer_id"],
                    batch["crop_id"],
                    batch["planting_date"],
                    batch["harvest_date"],
                    batch["fertilizer_summary"],
                    batch["acreage"],
                    batch["batch_notes"],
                    created_at,
                ),
            )

            previous_hash = "GENESIS"
            planting_date = datetime.fromisoformat(batch["planting_date"])
            harvest_date = datetime.fromisoformat(batch["harvest_date"])
            timeline = [
                (event_type, planting_date + timedelta(days=offset), details)
                for event_type, offset, details in LEDGER_EVENTS
            ]

            for event_type, event_date, details in timeline:
                event_date_iso = event_date.date().isoformat()
                event_hash = compute_event_hash(batch["id"], event_type, event_date_iso, details, previous_hash)
                connection.execute(
                    """
                    INSERT INTO ledger_events (
                        batch_id, event_type, event_date, details, previous_hash, event_hash, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        batch["id"],
                        event_type,
                        event_date_iso,
                        details,
                        previous_hash,
                        event_hash,
                        created_at,
                    ),
                )
                previous_hash = event_hash


def ensure_iot_db() -> None:
    IOT_DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    with get_iot_connection() as connection:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS iot_telemetry (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                device_id TEXT NOT NULL,
                farmer_name TEXT NOT NULL,
                farm_name TEXT NOT NULL,
                soil_moisture REAL NOT NULL,
                temperature REAL NOT NULL,
                humidity REAL NOT NULL,
                nitrogen REAL,
                phosphorus REAL,
                potassium REAL,
                moisture_threshold REAL NOT NULL,
                recorded_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS iot_alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telemetry_id INTEGER NOT NULL,
                device_id TEXT NOT NULL,
                farmer_name TEXT NOT NULL,
                farm_name TEXT NOT NULL,
                alert_type TEXT NOT NULL,
                severity TEXT NOT NULL,
                message TEXT NOT NULL,
                channel TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (telemetry_id) REFERENCES iot_telemetry(id),
                UNIQUE (telemetry_id, alert_type)
            );
            """
        )

        if connection.execute("SELECT COUNT(*) FROM iot_telemetry").fetchone()[0]:
            return

        now = datetime.utcnow()
        for sample in IOT_SEEDS:
            record_iot_telemetry(
                connection,
                sample,
                recorded_at=(now - timedelta(minutes=sample["sample_offset_minutes"])).isoformat(timespec="seconds") + "Z",
                create_alerts=False,
            )

        scan_iot_alerts(connection)


def record_iot_telemetry(
    connection: sqlite3.Connection,
    payload: dict[str, object],
    *,
    recorded_at: str | None = None,
    create_alerts: bool = True,
) -> dict[str, object]:
    timestamp = recorded_at or datetime.utcnow().isoformat(timespec="seconds") + "Z"

    def optional_float(value: object) -> float | None:
        if value in (None, ""):
            return None
        return float(value)

    cursor = connection.execute(
        """
        INSERT INTO iot_telemetry (
            device_id, farmer_name, farm_name, soil_moisture, temperature, humidity,
            nitrogen, phosphorus, potassium, moisture_threshold, recorded_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            str(payload["device_id"]),
            str(payload["farmer_name"]),
            str(payload["farm_name"]),
            float(payload["soil_moisture"]),
            float(payload["temperature"]),
            float(payload["humidity"]),
            optional_float(payload.get("nitrogen")),
            optional_float(payload.get("phosphorus")),
            optional_float(payload.get("potassium")),
            float(payload.get("moisture_threshold", IOT_DEFAULT_THRESHOLD)),
            timestamp,
        ),
    )
    telemetry_id = cursor.lastrowid

    if create_alerts:
        scan_iot_alerts(connection, telemetry_id=telemetry_id)

    return {
        "id": telemetry_id,
        "recorded_at": timestamp,
    }


def build_iot_alert_message(row: sqlite3.Row) -> tuple[str, str, str, str]:
    moisture = float(row["soil_moisture"])
    threshold = float(row["moisture_threshold"])
    deficit = threshold - moisture
    message = (
        f"Soil moisture is {moisture:.1f}% on {row['farm_name']} ({row['device_id']}). "
        f"Irrigation recommended to recover the {deficit:.1f}% deficit."
    )
    return message, "high", "irrigation", "notification"


def scan_iot_alerts(
    connection: sqlite3.Connection | None = None,
    *,
    telemetry_id: int | None = None,
) -> int:
    close_connection = False
    if connection is None:
        connection = get_iot_connection()
        close_connection = True

    try:
        if telemetry_id is not None:
            rows = connection.execute(
                """
                SELECT * FROM iot_telemetry
                WHERE id = ? AND soil_moisture < moisture_threshold
                """,
                (telemetry_id,),
            ).fetchall()
        else:
            rows = connection.execute(
                """
                SELECT t.*
                FROM iot_telemetry t
                LEFT JOIN iot_alerts a
                  ON a.telemetry_id = t.id AND a.alert_type = 'irrigation'
                WHERE t.soil_moisture < t.moisture_threshold AND a.id IS NULL
                ORDER BY t.recorded_at DESC
                """
            ).fetchall()

        created = 0
        for row in rows:
            existing = connection.execute(
                "SELECT 1 FROM iot_alerts WHERE telemetry_id = ? AND alert_type = 'irrigation'",
                (row["id"],),
            ).fetchone()
            if existing:
                continue

            message, severity, alert_type, channel = build_iot_alert_message(row)
            connection.execute(
                """
                INSERT INTO iot_alerts (
                    telemetry_id, device_id, farmer_name, farm_name, alert_type,
                    severity, message, channel, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    row["id"],
                    row["device_id"],
                    row["farmer_name"],
                    row["farm_name"],
                    alert_type,
                    severity,
                    message,
                    channel,
                    datetime.utcnow().isoformat(timespec="seconds") + "Z",
                ),
            )
            created += 1

        if created:
            connection.commit()
        return created
    finally:
        if close_connection:
            connection.close()


def get_iot_devices() -> list[dict[str, object]]:
    with get_iot_connection() as connection:
        rows = connection.execute(
            """
            SELECT device_id, farmer_name, farm_name, MAX(recorded_at) AS latest_recorded_at
            FROM iot_telemetry
            GROUP BY device_id, farmer_name, farm_name
            ORDER BY latest_recorded_at DESC
            """
        ).fetchall()

    return [
        {
            "device_id": row["device_id"],
            "farmer_name": row["farmer_name"],
            "farm_name": row["farm_name"],
            "latest_recorded_at": row["latest_recorded_at"],
        }
        for row in rows
    ]


def get_latest_device_id() -> str | None:
    devices = get_iot_devices()
    return devices[0]["device_id"] if devices else None


def get_device_telemetry(device_id: str | None, limit: int = 12) -> dict[str, object] | None:
    if not device_id:
        device_id = get_latest_device_id()
        if not device_id:
            return None

    with get_iot_connection() as connection:
        device = connection.execute(
            """
            SELECT device_id, farmer_name, farm_name, moisture_threshold, MAX(recorded_at) AS latest_recorded_at
            FROM iot_telemetry
            WHERE device_id = ?
            GROUP BY device_id, farmer_name, farm_name, moisture_threshold
            """,
            (device_id,),
        ).fetchone()

        if device is None:
            return None

        rows = connection.execute(
            """
            SELECT id, device_id, farmer_name, farm_name, soil_moisture, temperature, humidity,
                   nitrogen, phosphorus, potassium, moisture_threshold, recorded_at
            FROM iot_telemetry
            WHERE device_id = ?
            ORDER BY recorded_at DESC, id DESC
            LIMIT ?
            """,
            (device_id, limit),
        ).fetchall()

        alerts = connection.execute(
            """
            SELECT telemetry_id, device_id, farmer_name, farm_name, alert_type, severity,
                   message, channel, created_at
            FROM iot_alerts
            WHERE device_id = ?
            ORDER BY created_at DESC, id DESC
            LIMIT 10
            """,
            (device_id,),
        ).fetchall()

    history = [
        {
            "id": row["id"],
            "recorded_at": row["recorded_at"],
            "soil_moisture": row["soil_moisture"],
            "temperature": row["temperature"],
            "humidity": row["humidity"],
            "nitrogen": row["nitrogen"],
            "phosphorus": row["phosphorus"],
            "potassium": row["potassium"],
            "moisture_threshold": row["moisture_threshold"],
        }
        for row in rows
    ][::-1]

    current = history[-1] if history else None
    irrigation_needed = bool(current and current["soil_moisture"] < current["moisture_threshold"])
    fertilizer_needed = bool(
        current and min(
            float(current["nitrogen"] or 0),
            float(current["phosphorus"] or 0),
            float(current["potassium"] or 0),
        ) < 18
    )

    return {
        "device": {
            "device_id": device["device_id"],
            "farmer_name": device["farmer_name"],
            "farm_name": device["farm_name"],
            "moisture_threshold": device["moisture_threshold"],
            "latest_recorded_at": device["latest_recorded_at"],
        },
        "current": current,
        "history": history,
        "alerts": [
            {
                "telemetry_id": row["telemetry_id"],
                "device_id": row["device_id"],
                "farmer_name": row["farmer_name"],
                "farm_name": row["farm_name"],
                "alert_type": row["alert_type"],
                "severity": row["severity"],
                "message": row["message"],
                "channel": row["channel"],
                "created_at": row["created_at"],
            }
            for row in alerts
        ],
        "recommendations": {
            "irrigation_needed": irrigation_needed,
            "fertilizer_needed": fertilizer_needed,
            "fertilizer_hint": "NPK levels are trending low; schedule a nutrient check." if fertilizer_needed else "NPK levels are in a healthy range.",
        },
    }


def iot_alert_worker_loop(interval_seconds: int = IOT_WORKER_INTERVAL_SECONDS) -> None:
    while True:
        scan_iot_alerts()
        threading.Event().wait(interval_seconds)


def start_iot_alert_worker(interval_seconds: int = IOT_WORKER_INTERVAL_SECONDS) -> threading.Thread:
    worker = threading.Thread(target=iot_alert_worker_loop, kwargs={"interval_seconds": interval_seconds}, daemon=True)
    worker.start()
    return worker


def fetch_batch_detail(batch_id: int) -> dict[str, object] | None:
    with get_traceability_connection() as connection:
        batch = connection.execute(
            """
            SELECT
                b.id,
                b.batch_code,
                b.planting_date,
                b.harvest_date,
                b.fertilizer_summary,
                b.acreage,
                b.batch_notes,
                b.created_at,
                f.name AS farmer_name,
                f.location AS farmer_location,
                c.name AS crop_name,
                c.variety AS crop_variety
            FROM batches b
            JOIN farmers f ON f.id = b.farmer_id
            JOIN crops c ON c.id = b.crop_id
            WHERE b.id = ?
            """,
            (batch_id,),
        ).fetchone()

        if batch is None:
            return None

        events = connection.execute(
            """
            SELECT event_type, event_date, details, previous_hash, event_hash
            FROM ledger_events
            WHERE batch_id = ?
            ORDER BY id ASC
            """,
            (batch_id,),
        ).fetchall()

    trace_url = f"/verify-produce?batch_id={batch_id}"
    return {
        "batch": {
            "id": batch["id"],
            "batch_code": batch["batch_code"],
            "planting_date": batch["planting_date"],
            "harvest_date": batch["harvest_date"],
            "fertilizer_summary": batch["fertilizer_summary"],
            "acreage": batch["acreage"],
            "batch_notes": batch["batch_notes"],
            "created_at": batch["created_at"],
            "farmer": {
                "name": batch["farmer_name"],
                "location": batch["farmer_location"],
            },
            "crop": {
                "name": batch["crop_name"],
                "variety": batch["crop_variety"],
            },
            "trace_url": trace_url,
        },
        "events": [
            {
                "event_type": event["event_type"],
                "event_date": event["event_date"],
                "details": event["details"],
                "previous_hash": event["previous_hash"],
                "event_hash": event["event_hash"],
            }
            for event in events
        ],
    }


ensure_traceability_db()
ensure_iot_db()


@app.get("/health")
def health() -> tuple[dict[str, str], int]:
    return {"status": "ok"}, 200


@app.post("/predict_roi")
def predict_roi() -> tuple[dict[str, object], int]:
    payload = request.get_json(silent=True) or {}

    try:
        acreage = float(payload["acreage"])
        seed_cost = float(payload["seed_cost"])
        fertilizer_cost = float(payload["fertilizer_cost"])
        budget = float(payload["budget"])
        soil_type = str(payload["soil_type"])
        target_crop = str(payload["target_crop"])
    except (KeyError, TypeError, ValueError):
        return jsonify({"error": "Invalid forecast payload."}), 400

    if acreage <= 0 or seed_cost < 0 or fertilizer_cost < 0 or budget < 0:
        return jsonify({"error": "Input values must be positive."}), 400

    frame = pd.DataFrame([
        {
            "acreage": acreage,
            "seed_cost": seed_cost,
            "fertilizer_cost": fertilizer_cost,
            "budget": budget,
            "soil_type": soil_type,
            "target_crop": target_crop,
        }
    ])

    predicted_yield = float(MODEL.predict(frame)[0])
    crop_price = PRICE_PER_TON.get(target_crop, 380)
    projected_revenue = predicted_yield * crop_price
    total_costs = seed_cost + fertilizer_cost
    expected_profit = projected_revenue - total_costs
    roi_percent = (expected_profit / total_costs * 100) if total_costs else 0.0

    return jsonify(
        {
            "predicted_yield_tons": round(predicted_yield, 2),
            "projected_revenue": round(projected_revenue, 2),
            "total_costs": round(total_costs, 2),
            "expected_profit": round(expected_profit, 2),
            "roi_percent": round(roi_percent, 2),
            "budget_gap": round(budget - total_costs, 2),
            "crop_price_per_ton": crop_price,
        }
    ), 200


@app.get("/api/produce/batches")
def list_produce_batches() -> tuple[dict[str, object], int]:
    with get_traceability_connection() as connection:
        batches = connection.execute(
            """
            SELECT b.id, b.batch_code, b.planting_date, b.harvest_date, b.acreage,
                   f.name AS farmer_name, c.name AS crop_name
            FROM batches b
            JOIN farmers f ON f.id = b.farmer_id
            JOIN crops c ON c.id = b.crop_id
            ORDER BY b.id ASC
            """
        ).fetchall()

    return jsonify(
        {
            "batches": [
                {
                    "id": batch["id"],
                    "batch_code": batch["batch_code"],
                    "planting_date": batch["planting_date"],
                    "harvest_date": batch["harvest_date"],
                    "acreage": batch["acreage"],
                    "farmer_name": batch["farmer_name"],
                    "crop_name": batch["crop_name"],
                    "verify_url": f"/verify-produce?batch_id={batch['id']}",
                }
                for batch in batches
            ]
        }
    ), 200


@app.get("/api/produce/batches/<int:batch_id>")
def get_produce_batch(batch_id: int) -> tuple[dict[str, object], int]:
    detail = fetch_batch_detail(batch_id)
    if detail is None:
        return jsonify({"error": "Batch not found."}), 404
    return jsonify(detail), 200


@app.post("/api/iot/telemetry")
def ingest_iot_telemetry() -> tuple[dict[str, object], int]:
    payload = request.get_json(silent=True) or {}
    required_fields = ["device_id", "farmer_name", "farm_name", "soil_moisture", "temperature", "humidity"]

    missing_fields = [field for field in required_fields if field not in payload]
    if missing_fields:
        return jsonify({"error": "Missing telemetry fields.", "missing_fields": missing_fields}), 400

    try:
        telemetry_payload = {
            "device_id": str(payload["device_id"]),
            "farmer_name": str(payload["farmer_name"]),
            "farm_name": str(payload["farm_name"]),
            "soil_moisture": float(payload["soil_moisture"]),
            "temperature": float(payload["temperature"]),
            "humidity": float(payload["humidity"]),
            "nitrogen": float(payload["nitrogen"]) if payload.get("nitrogen") is not None else None,
            "phosphorus": float(payload["phosphorus"]) if payload.get("phosphorus") is not None else None,
            "potassium": float(payload["potassium"]) if payload.get("potassium") is not None else None,
            "moisture_threshold": float(payload.get("moisture_threshold", IOT_DEFAULT_THRESHOLD)),
        }
    except (TypeError, ValueError):
        return jsonify({"error": "Telemetry values must be numeric where expected."}), 400

    if telemetry_payload["soil_moisture"] < 0 or telemetry_payload["humidity"] < 0:
        return jsonify({"error": "Moisture and humidity must be non-negative."}), 400

    with get_iot_connection() as connection:
        stored = record_iot_telemetry(connection, telemetry_payload, create_alerts=False)
        created_alerts = scan_iot_alerts(connection, telemetry_id=stored["id"])

    dashboard = get_device_telemetry(telemetry_payload["device_id"])
    return jsonify(
        {
            "message": "Telemetry stored.",
            "telemetry_id": stored["id"],
            "recorded_at": stored["recorded_at"],
            "alerts_created": created_alerts,
            "irrigation_alert": telemetry_payload["soil_moisture"] < telemetry_payload["moisture_threshold"],
            "dashboard": dashboard,
        }
    ), 201


@app.get("/api/iot/devices")
def list_iot_devices() -> tuple[dict[str, object], int]:
    return jsonify({"devices": get_iot_devices()}), 200


@app.get("/api/iot/dashboard")
def get_iot_dashboard() -> tuple[dict[str, object], int]:
    device_id = request.args.get("device_id")
    dashboard = get_device_telemetry(device_id)
    if dashboard is None:
        return jsonify({"error": "No telemetry found for the requested device."}), 404
    return jsonify(dashboard), 200


@app.get("/api/iot/alerts")
def list_iot_alerts() -> tuple[dict[str, object], int]:
    device_id = request.args.get("device_id")
    limit = int(request.args.get("limit", 20))

    with get_iot_connection() as connection:
        if device_id:
            rows = connection.execute(
                """
                SELECT telemetry_id, device_id, farmer_name, farm_name, alert_type, severity,
                       message, channel, created_at
                FROM iot_alerts
                WHERE device_id = ?
                ORDER BY created_at DESC, id DESC
                LIMIT ?
                """,
                (device_id, limit),
            ).fetchall()
        else:
            rows = connection.execute(
                """
                SELECT telemetry_id, device_id, farmer_name, farm_name, alert_type, severity,
                       message, channel, created_at
                FROM iot_alerts
                ORDER BY created_at DESC, id DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()

    return jsonify(
        {
            "alerts": [
                {
                    "telemetry_id": row["telemetry_id"],
                    "device_id": row["device_id"],
                    "farmer_name": row["farmer_name"],
                    "farm_name": row["farm_name"],
                    "alert_type": row["alert_type"],
                    "severity": row["severity"],
                    "message": row["message"],
                    "channel": row["channel"],
                    "created_at": row["created_at"],
                }
                for row in rows
            ]
        }
    ), 200


@app.get("/verify-produce")
def verify_produce_entry() -> object:
    return send_from_directory(PROJECT_ROOT, "verify-produce.html")


@app.get("/trace.html")
def trace_entry() -> object:
    return send_from_directory(PROJECT_ROOT, "trace.html")


@app.get("/farm_dashboard.html")
def farm_dashboard_entry() -> object:
    return send_from_directory(PROJECT_ROOT, "farm_dashboard.html")


@app.get("/notifications.html")
def notifications_entry() -> object:
    return send_from_directory(PROJECT_ROOT, "notifications.html")


if __name__ == "__main__":
    start_iot_alert_worker()
    app.run(host="127.0.0.1", port=5000, debug=True, use_reloader=False)