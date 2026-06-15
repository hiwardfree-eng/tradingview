from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Key(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(32), unique=True, nullable=False, index=True)
    label = db.Column(db.String(64), default="")
    created_at = db.Column(db.Float, default=lambda: datetime.utcnow().timestamp())
    expires_at = db.Column(db.Float, default=0)
    active = db.Column(db.Boolean, default=True)
    used_count = db.Column(db.Integer, default=0)
    last_used = db.Column(db.Float, default=0)
    notes = db.Column(db.Text, default="")

class Log(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    event = db.Column(db.String(128), nullable=False)
    detail = db.Column(db.Text, default="")
    level = db.Column(db.String(16), default="info")
    timestamp = db.Column(db.String(32), default=lambda: datetime.utcnow().isoformat())

def init_db(app):
    db.create_all()
    if Log.query.count() == 0:
        db.session.add(Log(event="system_start", detail="TradingView initialized"))
        db.session.commit()
