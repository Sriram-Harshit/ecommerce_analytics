/**
 * ENTERPRISE E-COMMERCE ANALYTICS CHARTS & SIMULATOR ENGINE
 */

document.addEventListener("DOMContentLoaded", function () {
  // Initialize charts safely if their respective elements exist
  initOrdersTimeChart();
  initRevenueCategoryChart();
  initDeliveryDelayChart();
  initAovChart();
  initTopSellersChart();
  initMLSimulator();
});

/* =========================================================
   THEME PALETTE & UTILITIES
   ========================================================= */
const PALETTE = {
  primary: "#6366f1",
  primarySoft: "rgba(99, 102, 241, 0.18)",
  cyan: "#06b6d4",
  cyanSoft: "rgba(6, 182, 212, 0.18)",
  emerald: "#10b981",
  emeraldSoft: "rgba(16, 185, 129, 0.18)",
  amber: "#f59e0b",
  amberSoft: "rgba(245, 158, 11, 0.18)",
  rose: "#f43f5e",
  roseSoft: "rgba(244, 63, 94, 0.18)",
  purple: "#a855f7",
  grid: "rgba(255, 255, 255, 0.05)",
  textMuted: "#94a3b8",
  textMain: "#f8fafc",
};

function getJsonPayload(elementId) {
  const el = document.getElementById(elementId);
  if (!el) return null;
  try {
    return JSON.parse(el.textContent);
  } catch (e) {
    console.warn("Failed to parse JSON payload for", elementId, e);
    return null;
  }
}

function formatBRL(value) {
  return "R$ " + Number(value).toLocaleString("pt-BR", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

function getCommonChartOptions() {
  return {
    responsive: true,
    maintainAspectRatio: false,
    animation: { duration: 600, easing: "easeOutQuart" },
    plugins: {
      legend: {
        labels: {
          color: PALETTE.textMain,
          font: { family: "'Plus Jakarta Sans', sans-serif", size: 12 },
        },
      },
      tooltip: {
        backgroundColor: "rgba(15, 23, 42, 0.95)",
        titleColor: "#ffffff",
        bodyColor: "#e2e8f0",
        borderColor: "rgba(255, 255, 255, 0.1)",
        borderWidth: 1,
        padding: 10,
        boxPadding: 4,
        cornerRadius: 8,
      },
    },
    scales: {
      x: {
        ticks: { color: PALETTE.textMuted, font: { size: 11 } },
        grid: { color: PALETTE.grid },
      },
      y: {
        ticks: { color: PALETTE.textMuted, font: { size: 11 } },
        grid: { color: PALETTE.grid },
      },
    },
  };
}

/* =========================================================
   1. ORDER VOLUME TREND (BY YEAR)
   ========================================================= */
function initOrdersTimeChart() {
  const canvas = document.getElementById("ordersTimeChart");
  const rawData = getJsonPayload("orders-time-data");
  if (!canvas || !rawData) return;

  const years = [...new Set(rawData.map((d) => d.year))].sort();
  let activeYear = years[years.length - 1]; // Default to latest year
  let chartInstance = null;

  const navContainer = document.getElementById("yearNavContainer");
  if (navContainer) {
    navContainer.innerHTML = "";
    years.forEach((yr) => {
      const btn = document.createElement("button");
      btn.className = `year-btn ${yr === activeYear ? "active" : ""}`;
      btn.textContent = yr;
      btn.onclick = () => {
        document.querySelectorAll(".year-btn").forEach((b) => b.classList.remove("active"));
        btn.classList.add("active");
        activeYear = yr;
        renderYear(activeYear);
      };
      navContainer.appendChild(btn);
    });
  }

  function renderYear(year) {
    const monthNames = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
    const yearRecords = rawData.filter((d) => d.year === year);
    
    // Fill all 12 months cleanly
    const monthMap = {};
    yearRecords.forEach((d) => { monthMap[d.month] = d.order_count; });

    const labels = monthNames;
    const values = monthNames.map((_, idx) => monthMap[idx + 1] || 0);

    if (chartInstance) chartInstance.destroy();

    const ctx = canvas.getContext("2d");
    const gradient = ctx.createLinearGradient(0, 0, 0, 300);
    gradient.addColorStop(0, "rgba(99, 102, 241, 0.45)");
    gradient.addColorStop(1, "rgba(99, 102, 241, 0.0)");

    chartInstance = new Chart(canvas, {
      type: "line",
      data: {
        labels: labels,
        datasets: [
          {
            label: `Orders in ${year}`,
            data: values,
            borderColor: PALETTE.primary,
            backgroundColor: gradient,
            borderWidth: 2.5,
            tension: 0.4,
            fill: true,
            pointRadius: 4,
            pointBackgroundColor: PALETTE.primary,
            pointHoverRadius: 6,
          },
        ],
      },
      options: {
        ...getCommonChartOptions(),
        plugins: {
          ...getCommonChartOptions().plugins,
          tooltip: {
            ...getCommonChartOptions().plugins.tooltip,
            callbacks: {
              label: (ctx) => ` Orders: ${ctx.parsed.y.toLocaleString()} units`,
            },
          },
        },
      },
    });
  }

  renderYear(activeYear);
}

/* =========================================================
   2. REVENUE CONTRIBUTION BY CATEGORY (HORIZONTAL BAR)
   ========================================================= */
function initRevenueCategoryChart() {
  const canvas = document.getElementById("revenueChart");
  const rawLabels = getJsonPayload("rev-cat-labels");
  const values = getJsonPayload("rev-cat-values");
  if (!canvas || !rawLabels || !values) return;

  // 10 distinct gradient-inspired hues
  const colors = [
    "#6366f1", "#06b6d4", "#10b981", "#f59e0b", "#ec4899",
    "#8b5cf6", "#3b82f6", "#14b8a6", "#f97316", "#a855f7"
  ];

  const shortLabels = rawLabels.map((l) => (l.length > 16 ? l.slice(0, 16) + "…" : l));

  new Chart(canvas, {
    type: "bar",
    data: {
      labels: shortLabels,
      datasets: [
        {
          label: "Product Revenue",
          data: values,
          backgroundColor: colors.slice(0, values.length),
          borderRadius: 6,
          barThickness: 16,
        },
      ],
    },
    options: {
      ...getCommonChartOptions(),
      indexAxis: "y",
      scales: {
        x: {
          ticks: {
            color: PALETTE.textMuted,
            callback: (v) => formatBRL(v),
          },
          grid: { color: PALETTE.grid },
        },
        y: {
          ticks: { color: PALETTE.textMain, font: { weight: "500" } },
          grid: { display: false },
        },
      },
      plugins: {
        legend: { display: false },
        tooltip: {
          ...getCommonChartOptions().plugins.tooltip,
          callbacks: {
            title: (items) => rawLabels[items[0].dataIndex],
            label: (ctx) => ` Gross Sales: ${formatBRL(ctx.parsed.x)}`,
          },
        },
      },
    },
  });
}

/* =========================================================
   3. DELIVERY PERFORMANCE BREAKDOWN (DOUGHNUT)
   ========================================================= */
function initDeliveryDelayChart() {
  const canvas = document.getElementById("delayChart");
  const labels = getJsonPayload("delay-labels");
  const values = getJsonPayload("delay-values");
  if (!canvas || !labels || !values) return;

  const total = values.reduce((a, b) => a + b, 0);
  const onTimeRatio = total > 0 ? (((values[0] + values[1]) / total) * 100).toFixed(1) : 0;

  new Chart(canvas, {
    type: "doughnut",
    data: {
      labels: labels,
      datasets: [
        {
          data: values,
          backgroundColor: [PALETTE.emerald, PALETTE.cyan, PALETTE.rose],
          borderWidth: 0,
          hoverOffset: 8,
          cutout: "70%",
        },
      ],
    },
    plugins: [
      {
        id: "centerStatusText",
        beforeDraw(chart) {
          const { ctx, chartArea } = chart;
          if (!chartArea) return;
          const x = (chartArea.left + chartArea.right) / 2;
          const y = (chartArea.top + chartArea.bottom) / 2;

          ctx.save();
          ctx.fillStyle = "#ffffff";
          ctx.font = "700 20px 'Outfit', sans-serif";
          ctx.textAlign = "center";
          ctx.textBaseline = "middle";
          ctx.fillText(`${onTimeRatio}%`, x, y - 8);

          ctx.fillStyle = PALETTE.textMuted;
          ctx.font = "500 11px 'Plus Jakarta Sans', sans-serif";
          ctx.fillText("SLA Met", x, y + 14);
          ctx.restore();
        },
      },
    ],
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          position: "bottom",
          labels: {
            color: PALETTE.textMain,
            usePointStyle: true,
            padding: 14,
          },
        },
        tooltip: {
          ...getCommonChartOptions().plugins.tooltip,
          callbacks: {
            label(ctx) {
              const val = ctx.raw;
              const pct = total > 0 ? ((val / total) * 100).toFixed(1) : 0;
              return ` ${ctx.label}: ${val.toLocaleString()} orders (${pct}%)`;
            },
          },
        },
      },
    },
  });
}

/* =========================================================
   4. AVERAGE ORDER VALUE (AOV) TIMELINE
   ========================================================= */
function initAovChart() {
  const canvas = document.getElementById("aovChart");
  const labels = getJsonPayload("aov-labels");
  const values = getJsonPayload("aov-values");
  if (!canvas || !labels || !values) return;

  const ctx = canvas.getContext("2d");
  const gradient = ctx.createLinearGradient(0, 0, 0, 300);
  gradient.addColorStop(0, "rgba(245, 158, 11, 0.35)");
  gradient.addColorStop(1, "rgba(245, 158, 11, 0.0)");

  new Chart(canvas, {
    type: "line",
    data: {
      labels: labels,
      datasets: [
        {
          label: "AOV Trend (R$)",
          data: values,
          borderColor: PALETTE.amber,
          backgroundColor: gradient,
          borderWidth: 2.5,
          tension: 0.35,
          fill: true,
          pointRadius: 3,
          pointBackgroundColor: PALETTE.amber,
        },
      ],
    },
    options: {
      ...getCommonChartOptions(),
      scales: {
        x: {
          ticks: { color: PALETTE.textMuted, maxRotation: 45, minRotation: 45 },
          grid: { color: PALETTE.grid },
        },
        y: {
          ticks: {
            color: PALETTE.textMuted,
            callback: (v) => formatBRL(v),
          },
          grid: { color: PALETTE.grid },
        },
      },
      plugins: {
        ...getCommonChartOptions().plugins,
        tooltip: {
          ...getCommonChartOptions().plugins.tooltip,
          callbacks: {
            label: (ctx) => ` Average Order Value: ${formatBRL(ctx.parsed.y)}`,
          },
        },
      },
    },
  });
}

/* =========================================================
   5. TOP SELLERS PERFORMANCE BAR CHART
   ========================================================= */
function initTopSellersChart() {
  const canvas = document.getElementById("topSellersChart");
  const labels = getJsonPayload("top-sellers-labels");
  const values = getJsonPayload("top-sellers-values");
  if (!canvas || !labels || !values) return;

  new Chart(canvas, {
    type: "bar",
    data: {
      labels: labels,
      datasets: [
        {
          label: "Seller Gross Revenue",
          data: values,
          backgroundColor: [PALETTE.primary, PALETTE.cyan, PALETTE.emerald, PALETTE.amber, PALETTE.purple],
          borderRadius: 8,
          barThickness: 22,
        },
      ],
    },
    options: {
      ...getCommonChartOptions(),
      plugins: {
        legend: { display: false },
        tooltip: {
          ...getCommonChartOptions().plugins.tooltip,
          callbacks: {
            label: (ctx) => ` Revenue: ${formatBRL(ctx.parsed.y)}`,
          },
        },
      },
      scales: {
        x: { ticks: { color: PALETTE.textMain }, grid: { display: false } },
        y: {
          ticks: { color: PALETTE.textMuted, callback: (v) => formatBRL(v) },
          grid: { color: PALETTE.grid },
        },
      },
    },
  });
}

/* =========================================================
   6. INTERACTIVE ML DELAY PREDICTION SIMULATOR
   ========================================================= */
function initMLSimulator() {
  const freightInput = document.getElementById("simFreight");
  const priceInput = document.getElementById("simPrice");
  const itemsInput = document.getElementById("simItems");
  const installmentsInput = document.getElementById("simInstallments");

  if (!freightInput || !priceInput) return;

  const freightDisplay = document.getElementById("dispFreight");
  const priceDisplay = document.getElementById("dispPrice");
  const itemsDisplay = document.getElementById("dispItems");
  const installmentsDisplay = document.getElementById("dispInstallments");

  const probVal = document.getElementById("simProbVal");
  const probCircle = document.getElementById("simProbCircle");
  const riskBadge = document.getElementById("simRiskBadge");
  const recommendation = document.getElementById("simRecommendation");

  function syncAndPredict() {
    if (freightDisplay) freightDisplay.textContent = formatBRL(freightInput.value);
    if (priceDisplay) priceDisplay.textContent = formatBRL(priceInput.value);
    if (itemsDisplay) itemsDisplay.textContent = `${itemsInput.value} item(s)`;
    if (installmentsDisplay) installmentsDisplay.textContent = `${installmentsInput.value}x`;

    const payload = {
      freight_value: parseFloat(freightInput.value),
      price: parseFloat(priceInput.value),
      item_count: parseInt(itemsInput.value),
      installments: parseInt(installmentsInput.value),
    };

    fetch("/api/predict-delay/", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    })
      .then((res) => res.json())
      .then((data) => {
        if (data.probability_percent !== undefined) {
          if (probVal) probVal.textContent = `${data.probability_percent}%`;
          if (riskBadge) {
            riskBadge.textContent = data.risk_level;
            riskBadge.className = `risk-badge badge-${data.badge_class}`;
          }
          if (probCircle) {
            probCircle.className = `probability-circle ${data.badge_class}`;
          }
          if (recommendation) {
            recommendation.textContent = data.recommendation;
          }
        }
      })
      .catch((err) => console.error("Simulator API error:", err));
  }

  // Bind debounced listener
  let debounceTimer = null;
  [freightInput, priceInput, itemsInput, installmentsInput].forEach((input) => {
    input.addEventListener("input", () => {
      clearTimeout(debounceTimer);
      debounceTimer = setTimeout(syncAndPredict, 120);
    });
  });

  // Initial trigger
  syncAndPredict();
}
