const form = document.querySelector('#orderForm');
const status = document.querySelector('#formStatus');
let selectedOrder = null;
let refreshing = false;
async function api(path, options) {
  const response = await fetch('/api/' + path, options);
  if (!response.ok) throw new Error(`Request failed (${response.status})`);
  return response.json();
}
function list(id, rows, describe, select) {
  const target = document.getElementById(id);
  target.replaceChildren();
  if (!rows.length) { target.textContent = 'No records yet.'; return; }
  for (const row of rows) {
    const article = document.createElement('article'); article.className = 'row';
    const title = document.createElement(select ? 'button' : 'strong');
    const [heading, detail] = describe(row);
    title.textContent = heading;
    if (select) { title.type = 'button'; title.onclick = () => { selectedOrder = row.id; showTimeline().catch(showError); }; }
    const small = document.createElement('small'); small.textContent = detail;
    article.append(title, small); target.append(article);
  }
}
function showError(error) { status.textContent = error.message; }
async function showTimeline() {
  if (!selectedOrder) return;
  const order = await api('orders/' + encodeURIComponent(selectedOrder));
  document.getElementById('timelineTitle').textContent = `${order.id} · ${order.status}`;
  list('eventTimeline', order.timeline, event => [event.event_type,
    `${new Date(event.created_at).toLocaleString()}${event.reason ? ' · ' + event.reason : ''}`]);
}
async function refresh() {
  if (refreshing) return;
  refreshing = true;
  try {
    const [orders, inventory, payments, notifications] = await Promise.all(['orders','inventory','payments','notifications'].map(path => api(path)));
    for (const [id, rows] of [['orderCount',orders],['paymentCount',payments],['notificationCount',notifications]]) document.getElementById(id).textContent = rows.length;
    list('orders', orders, row => [`${row.id} · ${row.status}`, row.customer_id], true);
    list('inventory', inventory, row => [row.product_id, `${row.quantity} units available`]);
    list('payments', payments, row => [row.order_id, `${row.status} · simulated payment`]);
    list('notifications', notifications, row => [row.order_id, `${row.event_type} · local record`]);
    await showTimeline();
  } catch (error) { showError(error); } finally { refreshing = false; }
}
form.addEventListener('submit', async event => {
  event.preventDefault();
  const button = form.querySelector('button'); button.disabled = true;
  status.textContent = 'Submitting order…';
  try {
    const order = await api('orders', {method:'POST', headers:{'Content-Type':'application/json', 'Idempotency-Key':crypto.randomUUID()}, body:JSON.stringify({customer_id:document.getElementById('customerId').value.trim(), items:[{product_id:document.getElementById('productId').value, quantity:Number(document.getElementById('quantity').value)}]})});
    selectedOrder = order.order_id;
    status.textContent = `Accepted ${order.order_id}. Processing asynchronously.`;
    await refresh();
  } catch (error) { showError(error); } finally { button.disabled = false; }
});
document.getElementById('refreshButton').addEventListener('click', refresh);
refresh(); setInterval(refresh, 3000);
