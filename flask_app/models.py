from datetime import datetime, timezone

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import event

db = SQLAlchemy()


class Asset(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(150), nullable=False)
    asset_type = db.Column(db.String(50), nullable=False)
    owner = db.Column(db.String(100), nullable=False)
    criticality = db.Column(db.Integer, nullable=False)
    description = db.Column(db.Text, nullable=True)

    risks = db.relationship(
        "Risk", backref="asset", lazy=True, cascade="all, delete-orphan"
    )


class Threat(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(150), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    description = db.Column(db.Text, nullable=True)

    risks = db.relationship(
        "Risk", backref="threat", lazy=True, cascade="all, delete-orphan"
    )


class Vulnerability(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(150), nullable=False)
    cve_id = db.Column(db.String(50), nullable=True)
    severity = db.Column(db.String(50), nullable=False)
    description = db.Column(db.Text, nullable=True)

    risks = db.relationship(
        "Risk", backref="vulnerability", lazy=True, cascade="all, delete-orphan"
    )


class Risk(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    risk_name = db.Column(db.String(255), nullable=False)
    asset_id = db.Column(db.Integer, db.ForeignKey("asset.id"), nullable=False)
    threat_id = db.Column(db.Integer, db.ForeignKey("threat.id"), nullable=False)
    vulnerability_id = db.Column(
        db.Integer, db.ForeignKey("vulnerability.id"), nullable=False
    )

    likelihood = db.Column(db.Integer, nullable=False)
    impact = db.Column(db.Integer, nullable=False)
    risk_score = db.Column(db.Integer, nullable=False)
    risk_level = db.Column(db.String(50), nullable=False)

    owner = db.Column(db.String(100), nullable=False)
    status = db.Column(db.String(50), nullable=False, default="Open")
    mitigation = db.Column(db.Text, nullable=True)

    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )


def calculate_risk_fields(mapper, connection, target):
    target.risk_score = target.likelihood * target.impact
    if target.risk_score >= 20:
        target.risk_level = "Critical"
    elif target.risk_score >= 12:
        target.risk_level = "High"
    elif target.risk_score >= 5:
        target.risk_level = "Medium"
    else:
        target.risk_level = "Low"


event.listen(Risk, "before_insert", calculate_risk_fields)
event.listen(Risk, "before_update", calculate_risk_fields)
