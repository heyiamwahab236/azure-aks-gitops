from datetime import datetime
from fastapi import FastAPI
from sqlmodel import Field, SQLModel, Session, select
from shared.runtime import Runtime, emit, now

runtime = Runtime('payment', 'payment.inventory-reserved')
engine = runtime.engine
app = FastAPI(title='Payment Service (simulation)', version='0.2.0')


class Payment(SQLModel, table=True):
    __tablename__ = 'payments'
    id: int | None = Field(default=None, primary_key=True)
    order_id: str
    status: str
    created_at: datetime


def pay(session, event):
    session.add(Payment(order_id=event['order_id'], status='completed', created_at=now()))
    emit(session, 'payment', {**event, 'event_type': 'payment.completed'})


runtime.install(app, pay)


@app.get('/payments')
def payments():
    with Session(engine) as session:
        return session.exec(select(Payment).order_by(Payment.created_at.desc()).limit(200)).all()
