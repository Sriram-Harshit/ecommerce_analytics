document.addEventListener("DOMContentLoaded", function () {
  renderOrdersOverTime();
  renderRevenueByCategory();
  renderDeliveryDelay();
  renderTopSellers();
  calculate_aov_over_time();
});

/* ======================================
   THEME COLORS (Dark Dashboard)
====================================== */
const THEME = {
  yellow: "#ffc107",
  yellowSoft: "rgba(255,193,7,0.18)",

  blue: "#4dabf7",
  blueSoft: "rgba(77,171,247,0.25)",

  green: "#2bff88",
  greenSoft: "rgba(43,255,136,0.25)",

  red: "#ff4d4f",
  redSoft: "rgba(255,77,79,0.25)",

  orange: "#ff922b",
  purple: "#845ef7",

  grid: "rgba(255,255,255,0.05)",
  textMuted: "#adb5bd",
  textMain: "#e9ecef",
};

/* ======================================
   UTILITIES
====================================== */
function getJsonData(id) {
  const el = document.getElementById(id);
  return el ? JSON.parse(el.textContent) : null;
}

function formatLabel(text) {
  return text.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
}

function shortenLabel(text, maxLength = 7) {
  const formatted = formatLabel(text);
  return formatted.length > maxLength
    ? formatted.slice(0, maxLength) + "…"
    : formatted;
}

function formatSeller(id) {
  return `Seller ${id.slice(0, 6).toUpperCase()}`;
}

function darkAxis() {
  return {
    ticks: { color: THEME.textMuted },
    grid: { color: THEME.grid },
  };
}

function interactionConfig() {
  return {
    interaction: {
      mode: "nearest",
      intersect: false,
    },
    hover: {
      mode: "nearest",
      intersect: false,
    },
    animation: {
      duration: 100,
    },
  };
}
/* ======================================
   ORDERS OVER TIME (LINE)
====================================== */
const renderOrdersOverTime = () => {
  const rawData = getJsonData("orders-time-data");
  if (!rawData) return;

  const years = [...new Set(rawData.map((d) => d.year))].sort();
  let currentYearIndex = years.length - 1;

  const ctx = document.getElementById("ordersTimeChart");
  const yearLabel = document.getElementById("currentYear");
  let chart = null;

  function draw(year) {
    const filtered = rawData.filter((d) => d.year === year);

    const labels = filtered.map((d) =>
      new Date(year, d.month - 1).toLocaleString("en", { month: "short" })
    );

    const values = filtered.map((d) => d.order_count);
    yearLabel.textContent = year;

    if (chart) chart.destroy();

    chart = new Chart(ctx, {
      type: "line",
      data: {
        labels,
        datasets: [
          {
            label: "Orders",
            data: values,
            borderColor: THEME.yellow,
            backgroundColor: THEME.yellowSoft,
            borderWidth: 2,
            tension: 0.45,
            fill: true,
            pointRadius: 3,
            pointHoverRadius: 6,
            pointBackgroundColor: THEME.yellow,
          },
        ],
      },
      options: {
        ...interactionConfig(),
        responsive: true,
        maintainAspectRatio: false,
        scales: {
          x: darkAxis(),
          y: darkAxis(),
        },
        plugins: {
          legend: { labels: { color: THEME.textMain } },
        },
      },
    });
  }

  draw(years[currentYearIndex]);

  document.getElementById("prevYear").onclick = () => {
    if (currentYearIndex > 0) draw(years[--currentYearIndex]);
  };

  document.getElementById("nextYear").onclick = () => {
    if (currentYearIndex < years.length - 1) draw(years[++currentYearIndex]);
  };
};

/* ======================================
   REVENUE BY CATEGORY (BAR)
====================================== */
const renderRevenueByCategory = () => {
  const rawLabels = getJsonData("rev-cat-labels");
  const values = getJsonData("rev-cat-values");
  if (!rawLabels || !values) return;

  const labels = rawLabels.map((l) => shortenLabel(l));

  new Chart(document.getElementById("revenueChart"), {
    type: "bar",
    data: {
      labels,
      datasets: [
        {
          label: "Revenue",
          data: values,
          backgroundColor: [
            THEME.blue,
            THEME.green,
            THEME.yellow,
            THEME.orange,
            THEME.purple,
            "#ff6b6b",
            "#20c997",
            "#74c0fc",
          ],
          borderRadius: 8,
          barThickness: 18,
        },
      ],
    },
    options: {
      indexAxis: "y",
      responsive: true,
      maintainAspectRatio: false,
      ...interactionConfig(),

      scales: {
        x: {
          ...darkAxis(),
          ticks: {
            color: THEME.textMuted,
            callback: (v) => "₹" + v.toLocaleString(),
          },
          grid: { display: false },
        },
        y: darkAxis(),
      },
      plugins: {
        tooltip: {
          callbacks: {
            title: (items) => formatLabel(rawLabels[items[0].dataIndex]),
            label: (ctx) => `₹${ctx.parsed.x.toLocaleString()}`,
          },
        },
      },
    },
  });
};

/* ======================================
   DELIVERY DELAY (DOUGHNUT)
====================================== */
const renderDeliveryDelay = () => {
  const labels = getJsonData("delay-labels");
  const values = getJsonData("delay-values");
  if (!labels || !values) return;

  new Chart(document.getElementById("delayChart"), {
    type: "doughnut",
    data: {
      labels,
      datasets: [
        {
          data: values,
          backgroundColor: [THEME.green, THEME.blue, THEME.red],
          borderWidth: 0,
          hoverOffset: 8,
          cutout: "65%",
        },
      ],
    },
    plugins: [
      {
        id: "centerText",
        beforeDraw(chart) {
          const { ctx, chartArea } = chart;
          const x = (chartArea.left + chartArea.right) / 2;
          const y = (chartArea.top + chartArea.bottom) / 2;

          ctx.save();
          ctx.fillStyle = THEME.yellow;
          ctx.font = "600 18px system-ui";
          ctx.textAlign = "center";
          ctx.textBaseline = "middle";
          ctx.fillText("Deliveries", x, y);
          ctx.restore();
        },
      },
    ],
    options: {
      responsive: true,
      maintainAspectRatio: false,
      ...interactionConfig(),

      plugins: {
        legend: {
          position: "bottom",
          labels: {
            color: THEME.textMain,
            usePointStyle: true,
          },
        },
        tooltip: {
          callbacks: {
            label(ctx) {
              const total = ctx.dataset.data.reduce((a, b) => a + b, 0);
              const percent = ((ctx.raw / total) * 100).toFixed(1);
              return `${ctx.label}: ${percent}%`;
            },
          },
        },
      },
    },
  });
};

/* ======================================
   TOP SELLERS (BAR)
====================================== */
const renderTopSellers = () => {
  const rawLabels = getJsonData("top-sellers-labels");
  const values = getJsonData("top-sellers-values");
  if (!rawLabels || !values) return;

  const labels = rawLabels.map((id) => formatSeller(id));

  new Chart(document.getElementById("topSellersChart"), {
    type: "bar",
    data: {
      labels,
      datasets: [
        {
          label: "Revenue",
          data: values,
          backgroundColor: values.map((_, i) => {
            const shades = [
              THEME.yellow,
              "#ffd43b",
              "#ffe066",
              "#fff3bf",
              "#ffec99",
              "#ffe066",
              "#ffd43b",
            ];
            return shades[i] || THEME.yellow;
          }),
          borderRadius: 6,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      ...interactionConfig(),
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: {
            title: (items) => `Seller ID: ${rawLabels[items[0].dataIndex]}`,
            label: (ctx) => `Revenue: ₹${ctx.parsed.y.toLocaleString()}`,
          },
        },
      },
      scales: {
        x: darkAxis(),
        y: darkAxis(),
      },
    },
  });
};

/* ======================================
    AOV OVER TIME (LINE)
====================================== */
const calculate_aov_over_time = () => {
  const labels = getJsonData("aov-labels");
  const values = getJsonData("aov-values");

  if (!labels || !values) return;

  const ctx = document.getElementById("aovChart");
  if (!ctx) return;

  new Chart(ctx, {
    type: "line",
    data: {
      labels,
      datasets: [
        {
          label: "Average Order Value",
          data: values,

          borderColor: THEME.orange,
          backgroundColor: "rgba(255,146,43,0.25)",

          borderWidth: 2,
          tension: 0.45,
          fill: true,

          pointRadius: 3,
          pointHoverRadius: 6,
          pointBackgroundColor: THEME.orange,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      ...interactionConfig(),

      scales: {
        x: darkAxis(),
        y: {
          ...darkAxis(),
          ticks: {
            color: THEME.textMuted,
            callback: (v) => "₹" + v.toLocaleString(),
          },
        },
      },

      plugins: {
        legend: {
          labels: {
            color: THEME.textMain,
          },
        },
        tooltip: {
          callbacks: {
            label: (ctx) => `AOV: ₹${ctx.parsed.y.toLocaleString()}`,
          },
        },
      },
    },
  });
};
