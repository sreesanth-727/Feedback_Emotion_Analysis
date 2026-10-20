/**
 * FeedbackIQ - Frontend JavaScript Interactions & Chart.js Visualizations
 * Sona College of Technology, CSE Dept
 */

document.addEventListener("DOMContentLoaded", function () {
  initMobileNav();
  initFlashDismiss();
  initClearModal();
  initSamplePrompts();
  initDropzone();
  initCharts();
});

/* ==========================================================================
   1. Mobile Navigation
   ========================================================================== */
function initMobileNav() {
  const toggleBtn = document.getElementById("mobileNavToggle");
  const navMenu = document.getElementById("navLinks");
  if (!toggleBtn || !navMenu) return;

  toggleBtn.addEventListener("click", function () {
    const isExpanded = navMenu.classList.toggle("show");
    toggleBtn.setAttribute("aria-expanded", isExpanded);
  });
}

/* ==========================================================================
   2. Flash Messages Dismissal
   ========================================================================== */
function initFlashDismiss() {
  document.querySelectorAll(".flash-dismiss").forEach(function (button) {
    button.addEventListener("click", function () {
      const flash = button.closest(".flash-message");
      if (flash) {
        flash.style.opacity = "0";
        flash.style.transform = "translateY(-6px)";
        setTimeout(() => flash.remove(), 200);
      }
    });
  });
}

/* ==========================================================================
   3. Clear History Confirmation Modal
   ========================================================================== */
function initClearModal() {
  const openButtons = document.querySelectorAll("[data-action='open-clear-modal']");
  const modal = document.getElementById("clearHistoryModal");
  const cancelButtons = document.querySelectorAll("[data-action='close-clear-modal']");

  if (!modal) return;

  function openModal(e) {
    if (e) e.preventDefault();
    modal.classList.add("show");
    modal.setAttribute("aria-hidden", "false");
    document.body.style.overflow = "hidden";
  }

  function closeModal() {
    modal.classList.remove("show");
    modal.setAttribute("aria-hidden", "true");
    document.body.style.overflow = "";
  }

  openButtons.forEach(btn => btn.addEventListener("click", openModal));
  cancelButtons.forEach(btn => btn.addEventListener("click", closeModal));

  modal.addEventListener("click", function (e) {
    if (e.target === modal) {
      closeModal();
    }
  });

  document.addEventListener("keydown", function (e) {
    if (e.key === "Escape" && modal.classList.contains("show")) {
      closeModal();
    }
  });
}

/* ==========================================================================
   4. Sample Prompts (Single Analysis Page)
   ========================================================================== */
function initSamplePrompts() {
  const textarea = document.getElementById("feedbackTextInput");
  const sampleButtons = document.querySelectorAll(".sample-btn[data-sample]");

  if (!textarea || sampleButtons.length === 0) return;

  sampleButtons.forEach(btn => {
    btn.addEventListener("click", function () {
      const text = btn.getAttribute("data-sample");
      if (text) {
        textarea.value = text;
        textarea.focus();
        // Trigger input event in case dynamic character count is attached
        textarea.dispatchEvent(new Event("input", { bubbles: true }));
      }
    });
  });
}

/* ==========================================================================
   5. File Upload Dropzone (Batch Upload Page)
   ========================================================================== */
function initDropzone() {
  const dropzone = document.getElementById("uploadDropzone");
  const fileInput = document.getElementById("fileInput");
  const filePill = document.getElementById("selectedFilePill");
  const fileNameText = document.getElementById("selectedFileName");
  const submitBtn = document.getElementById("uploadSubmitBtn");

  if (!dropzone || !fileInput) return;

  function updateFileInfo(file) {
    if (!file) return;
    if (filePill && fileNameText) {
      fileNameText.textContent = `${file.name} (${(file.size / 1024).toFixed(1)} KB)`;
      filePill.style.display = "inline-flex";
    }
    if (submitBtn) {
      submitBtn.removeAttribute("disabled");
    }
  }

  fileInput.addEventListener("change", function () {
    if (fileInput.files && fileInput.files[0]) {
      updateFileInfo(fileInput.files[0]);
    }
  });

  ["dragenter", "dragover"].forEach(eventName => {
    dropzone.addEventListener(eventName, function (e) {
      e.preventDefault();
      e.stopPropagation();
      dropzone.classList.add("dragover");
    }, false);
  });

  ["dragleave", "drop"].forEach(eventName => {
    dropzone.addEventListener(eventName, function (e) {
      e.preventDefault();
      e.stopPropagation();
      dropzone.classList.remove("dragover");
    }, false);
  });

  dropzone.addEventListener("drop", function (e) {
    const dt = e.dataTransfer;
    if (dt && dt.files && dt.files.length > 0) {
      fileInput.files = dt.files;
      updateFileInfo(dt.files[0]);
    }
  });
}

/* ==========================================================================
   6. Chart.js Dashboard Visualizations
   ========================================================================== */
function initCharts() {
  if (typeof Chart === "undefined") {
    console.warn("Chart.js library is not loaded.");
    return;
  }

  // Parse JSON data safely from DOM
  const chartDataScript = document.getElementById("chart-data");
  let chartPayload = null;

  if (chartDataScript) {
    try {
      chartPayload = JSON.parse(chartDataScript.textContent || "{}");
    } catch (err) {
      console.error("Failed to parse chart payload JSON:", err);
    }
  }

  // Global Chart.js defaults for consistent aesthetic
  Chart.defaults.font.family = "'Plus Jakarta Sans', -apple-system, sans-serif";
  Chart.defaults.color = "#475569";
  Chart.defaults.plugins.tooltip.backgroundColor = "#0f172a";
  Chart.defaults.plugins.tooltip.titleColor = "#ffffff";
  Chart.defaults.plugins.tooltip.bodyColor = "#e2e8f0";
  Chart.defaults.plugins.tooltip.padding = 10;
  Chart.defaults.plugins.tooltip.cornerRadius = 8;

  renderSentimentChart(chartPayload ? chartPayload.sentiments : null);
  renderEmotionChart(chartPayload ? chartPayload.emotions : null);
  renderCategoryChart(chartPayload ? chartPayload.categories : null);
}

/**
 * 6.1 Sentiment Donut Chart
 */
function renderSentimentChart(data) {
  const canvas = document.getElementById("sentimentChart");
  if (!canvas) return;

  let labels = ["Positive", "Neutral", "Negative"];
  let values = [0, 0, 0];

  if (data && Array.isArray(data.labels) && Array.isArray(data.data)) {
    labels = data.labels;
    values = data.data;
  } else if (data && typeof data === "object") {
    values = [
      data.Positive || data.positive || 0,
      data.Neutral || data.neutral || 0,
      data.Negative || data.negative || 0
    ];
  }

  const total = values.reduce((a, b) => a + Number(b), 0);

  new Chart(canvas, {
    type: "doughnut",
    data: {
      labels: labels,
      datasets: [
        {
          data: total > 0 ? values : [1, 1, 1],
          backgroundColor: total > 0 ? ["#10b981", "#94a3b8", "#f43f5e"] : ["#e2e8f0", "#e2e8f0", "#e2e8f0"],
          borderWidth: 2,
          borderColor: "#ffffff",
          hoverOffset: 6
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      cutout: "68%",
      plugins: {
        legend: {
          position: "bottom",
          labels: {
            boxWidth: 12,
            boxHeight: 12,
            padding: 16,
            usePointStyle: true,
            font: { weight: 600, size: 12 }
          }
        },
        tooltip: {
          callbacks: {
            label: function (ctx) {
              if (total === 0) return "No feedback recorded yet";
              const val = ctx.raw || 0;
              const pct = total > 0 ? ((val / total) * 100).toFixed(1) : "0.0";
              return ` ${ctx.label}: ${val} (${pct}%)`;
            }
          }
        }
      }
    }
  });
}

/**
 * 6.2 Emotion Bar Chart
 */
function renderEmotionChart(data) {
  const canvas = document.getElementById("emotionChart");
  if (!canvas) return;

  let labels = ["Joy", "Anger", "Sadness", "Fear", "Surprise", "Neutral"];
  let values = [0, 0, 0, 0, 0, 0];

  if (data && Array.isArray(data.labels) && Array.isArray(data.data)) {
    labels = data.labels;
    values = data.data;
  } else if (data && typeof data === "object") {
    values = labels.map(lbl => data[lbl] || data[lbl.toLowerCase()] || 0);
  }

  const emotionColors = [
    "#f59e0b", // Joy - amber
    "#ef4444", // Anger - red
    "#3b82f6", // Sadness - blue
    "#a855f7", // Fear - purple
    "#f97316", // Surprise - orange
    "#94a3b8"  // Neutral - slate
  ];

  new Chart(canvas, {
    type: "bar",
    data: {
      labels: labels,
      datasets: [
        {
          label: "Feedback Count",
          data: values,
          backgroundColor: emotionColors,
          borderRadius: 6,
          maxBarThickness: 34
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          display: false
        },
        tooltip: {
          callbacks: {
            label: function (ctx) {
              return ` ${ctx.parsed.y} feedbacks`;
            }
          }
        }
      },
      scales: {
        y: {
          beginAtZero: true,
          ticks: {
            precision: 0,
            font: { size: 11 }
          },
          grid: {
            color: "#f1f5f9"
          }
        },
        x: {
          grid: {
            display: false
          },
          ticks: {
            font: { weight: 600, size: 11 }
          }
        }
      }
    }
  });
}

/**
 * 6.3 Category Horizontal Bar Chart
 */
function renderCategoryChart(data) {
  const canvas = document.getElementById("categoryChart");
  if (!canvas) return;

  const defaultCategories = [
    "Product Quality",
    "Delivery",
    "Customer Service",
    "Payment",
    "Pricing",
    "Technical Issue",
    "Refund / Return"
  ];

  let labels = defaultCategories;
  let values = labels.map(() => 0);

  if (data && Array.isArray(data.labels) && Array.isArray(data.data)) {
    labels = data.labels;
    values = data.data;
  } else if (data && typeof data === "object") {
    const keys = Object.keys(data).filter(k => k !== "labels" && k !== "data" && k !== "datasets");
    if (keys.length > 0) {
      labels = keys;
      values = labels.map(lbl => data[lbl] || 0);
    }
  }

  new Chart(canvas, {
    type: "bar",
    data: {
      labels: labels,
      datasets: [
        {
          label: "Volume",
          data: values,
          backgroundColor: "#4f46e5",
          borderRadius: 6,
          maxBarThickness: 20
        }
      ]
    },
    options: {
      indexAxis: "y",
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          display: false
        },
        tooltip: {
          callbacks: {
            label: function (ctx) {
              return ` ${ctx.parsed.x} tickets`;
            }
          }
        }
      },
      scales: {
        x: {
          beginAtZero: true,
          ticks: {
            precision: 0,
            font: { size: 11 }
          },
          grid: {
            color: "#f1f5f9"
          }
        },
        y: {
          grid: {
            display: false
          },
          ticks: {
            font: { weight: 500, size: 12 }
          }
        }
      }
    }
  });
}
