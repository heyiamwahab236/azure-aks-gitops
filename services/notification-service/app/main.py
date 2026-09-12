from datetime import datetime
from fastapi import FastAPI
from sqlmodel import Field, SQLModel, Session, select
from shared.runtime import Runtime, now

runtime = Runtime('notification', 'notification.events')
engine = runtime.engine
app = FastAPI(title='Notification Service (record only)', version='0.2.0')


class Notification(SQLModel, table=True):
    __tablename__ = 'notifications'
    id: int | None = Field(default=None, primary_key=True)
    order_id: str
    event_type: str
    status: str
    created_at: datetime


def notify(session, event):
    session.add(Notification(order_id=event['order_id'], event_type=event['event_type'], status='recorded', created_at=now()))


runtime.install(app, notify)


@app.get('/notifications')
def notifications():
    with Session(engine) as session:
        return session.exec(select(Notification).order_by(Notification.created_at.desc()).limit(200)).all()
