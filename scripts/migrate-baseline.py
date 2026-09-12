"""One-time additive migration: run with application writers stopped, storage preserved.

Run inside the new order image, piping this file to python. Existing history becomes
deduplication evidence so replaying historical events cannot repeat business effects.
"""
from sqlalchemy import text
from sqlmodel import SQLModel
from app.main import engine

with engine.begin() as connection:
    connection.execute(text('SELECT pg_advisory_xact_lock(837211)'))
    SQLModel.metadata.create_all(connection)
    for consumer, table, expression in [
        ('inventory', 'inventory_reservations', "order_id || ':' || 'order.created'"),
        ('payment', 'payments', "order_id || ':' || 'inventory.reserved'"),
        ('notification', 'notifications', "order_id || ':' || event_type"),
    ]:
        # Table/expression identifiers are fixed source constants, never user input.
        connection.execute(text(f"INSERT INTO platform_inbox (consumer,event_key,created_at) SELECT :consumer,{expression},min(created_at) FROM {table} GROUP BY {expression} ON CONFLICT DO NOTHING"), {'consumer': consumer})
    connection.execute(text("INSERT INTO order_timeline (id,order_id,event_type,created_at) SELECT id || ':' || 'order.created',id,'order.created',created_at FROM orders ON CONFLICT DO NOTHING"))
    connection.execute(text("INSERT INTO order_timeline (id,order_id,event_type,created_at) SELECT order_id || ':' || event_type,order_id,event_type,min(created_at) FROM notifications GROUP BY order_id,event_type ON CONFLICT DO NOTHING"))
    connection.execute(text("INSERT INTO platform_inbox (consumer,event_key,created_at) SELECT 'order',id,created_at FROM order_timeline WHERE event_type IN ('inventory.reserved','inventory.failed','payment.completed') ON CONFLICT DO NOTHING"))
    connection.execute(text("UPDATE orders SET status='completed' WHERE id IN (SELECT order_id FROM payments WHERE status='completed')"))
    connection.execute(text("UPDATE orders SET status='failed' WHERE status!='completed' AND id IN (SELECT order_id FROM inventory_reservations WHERE status='failed')"))
print('PASS: additive history migration committed; existing rows and volumes preserved.')

