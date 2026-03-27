(function () {
  const data = window.STATUS_DATA;

  if (!data) {
    document.body.innerHTML = "<main style='padding:24px;font-family:sans-serif'>Missing dashboard data. Run <code>python3 scripts/build_status_dashboard.py</code>.</main>";
    return;
  }

  const statusLabels = {
    verified: "Verified",
    active: "Active",
    partial: "Partial",
    blocked: "Blocked",
  };

  function formatDate(isoString) {
    try {
      return new Date(isoString).toLocaleString([], {
        year: "numeric",
        month: "short",
        day: "numeric",
        hour: "2-digit",
        minute: "2-digit",
      });
    } catch (error) {
      return isoString;
    }
  }

  function el(tag, className, text) {
    const node = document.createElement(tag);
    if (className) {
      node.className = className;
    }
    if (text !== undefined) {
      node.textContent = text;
    }
    return node;
  }

  function appendList(parent, items) {
    const list = el("ul", "mini-list");
    items.forEach((item) => {
      const child = el("li", "", item);
      list.appendChild(child);
    });
    parent.appendChild(list);
  }

  function buildStatusPill(status) {
    const pill = el("span", `status-pill status-${status}`, statusLabels[status] || status);
    return pill;
  }

  function mountMetrics() {
    const container = document.getElementById("metrics");
    data.metrics.forEach((metric) => {
      const card = el("article", "metric");
      card.appendChild(el("p", "tile__label", metric.label));
      card.appendChild(el("strong", "metric__value", metric.value));
      card.appendChild(el("p", "metric__detail", metric.detail));
      container.appendChild(card);
    });
  }

  function mountWorkstreams() {
    const container = document.getElementById("workstreams");
    data.workstreams.forEach((item) => {
      const card = el("article", "workstream");
      const header = el("div", "workstream__header");
      const copy = el("div");
      copy.appendChild(el("p", "workstream__stage", item.stage));
      copy.appendChild(el("h3", "", item.name));
      header.appendChild(copy);
      header.appendChild(buildStatusPill(item.status));
      card.appendChild(header);
      card.appendChild(el("p", "workstream__summary", item.summary));
      appendList(card, item.bullets);

      const evidence = el("div", "evidence-list");
      item.evidence.forEach((link) => {
        const anchor = el("a", "evidence-link");
        anchor.href = link.href;
        anchor.textContent = link.label;
        anchor.title = link.path;
        evidence.appendChild(anchor);
      });
      card.appendChild(evidence);
      container.appendChild(card);
    });
  }

  function mountCards(containerId, items) {
    const container = document.getElementById(containerId);
    items.forEach((item) => {
      const card = el("article", "list-card");
      card.appendChild(el("p", "list-card__kicker", item.title));
      card.appendChild(el("p", "list-card__body", item.detail));
      container.appendChild(card);
    });
  }

  function mountSimpleList(containerId, items) {
    const container = document.getElementById(containerId);
    items.forEach((item) => {
      const card = el("article", "list-card");
      card.appendChild(el("p", "list-card__body", item));
      container.appendChild(card);
    });
  }

  function mountSources() {
    const container = document.getElementById("sources");
    data.sources.forEach((item) => {
      const anchor = el("a", "source-link");
      anchor.href = item.href;
      const left = el("div");
      left.appendChild(el("p", "list-card__kicker", item.label));
      left.appendChild(el("p", "list-card__body", item.path));
      const right = el("code", "source-link__meta", item.exists === "true" ? "present" : "missing");
      anchor.appendChild(left);
      anchor.appendChild(right);
      container.appendChild(anchor);
    });
  }

  document.getElementById("repo-name").textContent = data.repo.name;
  document.getElementById("headline").textContent = data.headline;
  document.getElementById("recommendation").textContent = data.recommendation;
  document.getElementById("generated-at").textContent = `Generated ${formatDate(data.generatedAt)} from live repo files and the local test suite.`;
  document.getElementById("refresh-command").textContent = data.refreshCommand;

  const overallStatus = document.getElementById("overall-status");
  overallStatus.textContent = statusLabels[data.health.status] || data.health.status;
  overallStatus.className = `status-pill status-${data.health.status}`;

  mountMetrics();
  mountWorkstreams();
  mountCards("focus-items", data.currentFocus);
  mountCards("blockers", data.blockers);
  mountSimpleList("doc-drift", data.docDrift);
  mountSimpleList("recent-changes", data.recentChanges);
  mountSources();
})();
