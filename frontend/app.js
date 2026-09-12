const form = document.querySelector("#orderForm");
const refreshButton = document.querySelector("#refreshButton");
const formStatus = document.querySelector("#formStatus");

const views = {
  orders: document.querySelector("#orders"),
  inventory: document.querySelector("#inventory"),
  payments: document.querySelector("#payments"),
  notifications: document.querySelector("#notifications"),
};

const counts = {
  orders: document.querySelector("#orderCount"),
  payments: document.querySelector("#paymentCount"),
  notifications: document.querySelector("#notificationCount"),
};

async function requestJson(url, options) {
  const response = await fetch(url, options);
  if (!response.ok) {
    throw new Error(`${response.status} ${response.statusText}`);
  }
  return response.json();
}

function renderList(target, rows, mapper) {
  if (!rows.length) {
    target.innerHTML = '<p class="empty">No records yet.</p>';
    return;
  }

  target.innerHTML = rows
    .map((row) => {
      const item = mapper(row);
      return `
        <article class="row">
          <strong>${item.title}</strong>
          <small>${item.detail}</small>
        </article>
      `;
    })
    .join("");
}

async function refresh() {
  const [orders, inventory, payments, notifications] = await Promise.all([
    requestJson("/api/orders"),
    requestJson("/api/inventory"),
    requestJson("/api/payments"),
    requestJson("/api/notifications"),
  ]);

  counts.orders.textContent = orders.length;
  counts.payments.textContent = payments.length;
  counts.notifications.textContent = notifications.length;

  renderList(views.orders, orders, (order) => ({
    title: `${order.id} · ${order.status}`,
    detail: `${order.customer_id} · ${new Date(order.created_at).toLocaleString()}`,
  }));

  renderList(views.inventory, inventory, (item) => ({
    title: item.product_id,
    detail: `${item.quantity} units available`,
  }));

  renderList(views.payments, payments, (payment) => ({
    title: `${payment.order_id} · ${payment.status}`,
    detail: new Date(payment.created_at).toLocaleString(),
  }));

  renderList(views.notifications, notifications, (notification) => ({
    title: `${notification.order_id} · ${notification.event_type}`,
    detail: `${notification.status} · ${new Date(notification.created_at).toLocaleString()}`,
  }));
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const payload = {
    customer_id: document.querySelector("#customerId").value,
    items: [
      {
        product_id: document.querySelector("#productId").value,
        quantity: Number(document.querySelector("#quantity").value),
      },
    ],
  };

  formStatus.textContent = "Creating order...";
  try {
    const order = await requestJson("/api/orders", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    formStatus.textContent = `Created ${order.order_id}`;
    setTimeout(refresh, 900);
  } catch (error) {
    formStatus.textContent = `Request failed: ${error.message}`;
  }
});

refreshButton.addEventListener("click", refresh);
refresh();
setInterval(refresh, 5000);
