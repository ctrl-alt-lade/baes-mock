/**
 * BAES CBT Portal - Admin Dashboard Logic
 * Handles PIN verification, candidate metrics, dynamic table rendering,
 * raw answer review modal, and CSV exports.
 */

(() => {
  // Application State
  let adminPin = sessionStorage.getItem("baes_admin_pin") || "";
  let allCandidates = [];
  let currentFilter = "all";
  let questionsMap = {}; // Cache of question details if available

  // DOM Elements
  const pinModal = document.getElementById("pin-modal");
  const pinForm = document.getElementById("pin-form");
  const pinInput = document.getElementById("pin-input");
  const pinAlert = document.getElementById("pin-alert");
  const pinSubmitBtn = document.getElementById("pin-submit-btn");
  const pinBtnText = document.getElementById("pin-btn-text");
  const pinSpinner = document.getElementById("pin-spinner");

  const mainDashboard = document.getElementById("main-dashboard");
  const searchInput = document.getElementById("search-input");
  const filterBtns = document.querySelectorAll(".filter-btn");
  const tableBody = document.getElementById("candidates-table-body");
  const tableEmpty = document.getElementById("table-empty");

  const btnExportCsv = document.getElementById("btn-export-csv");
  const btnRefresh = document.getElementById("btn-refresh");
  const btnLock = document.getElementById("btn-lock");

  // Metric Elements
  const metricTotal = document.getElementById("metric-total");
  const metricCompleted = document.getElementById("metric-completed");
  const metricPending = document.getElementById("metric-pending");
  const metricAvgGpa = document.getElementById("metric-avg-gpa");

  // Answers Modal Elements
  const answersModal = document.getElementById("answers-modal");
  const modalCandidateMatric = document.getElementById("modal-candidate-matric");
  const modalGpa = document.getElementById("modal-gpa");
  const modalScoresSummary = document.getElementById("modal-scores-summary");
  const modalAnsweredCount = document.getElementById("modal-answered-count");
  const modalAnswersContainer = document.getElementById("modal-answers-container");
  const btnCloseAnswers = document.getElementById("btn-close-answers");
  const btnCloseAnswersFooter = document.getElementById("btn-close-answers-footer");

  /**
   * Option index to alphabet letter conversion.
   */
  const OPTION_LETTERS = ["A", "B", "C", "D", "E"];

  /**
   * Pre-load question descriptions to enrich the submitted answers modal.
   */
  async function loadQuestionMeta() {
    try {
      const res = await fetch("/api/questions?matric_no=ADMIN");
      if (res.ok) {
        const data = await res.json();
        const questions = Array.isArray(data) ? data : (data.questions || []);
        questions.forEach((q) => {
          questionsMap[q.id] = q;
        });
      }
    } catch {
      // Questions endpoint non-blocking fallback
    }
  }

  /**
   * Set loading UI state on PIN submission.
   */
  function setPinLoading(isLoading) {
    if (pinSubmitBtn) pinSubmitBtn.disabled = isLoading;
    if (isLoading) {
      if (pinBtnText) pinBtnText.textContent = "Verifying PIN...";
      if (pinSpinner) pinSpinner.classList.remove("hidden");
    } else {
      if (pinBtnText) pinBtnText.textContent = "Authenticate Admin";
      if (pinSpinner) pinSpinner.classList.add("hidden");
    }
  }

  /**
   * Attempt PIN authentication against the dashboard endpoint.
   */
  async function authenticatePin(pin) {
    setPinLoading(true);
    if (pinAlert) pinAlert.classList.add("hidden");

    try {
      const response = await fetch(`/api/admin/dashboard?pin=${encodeURIComponent(pin)}`);

      if (response.status === 403) {
        throw new Error("Invalid administrator PIN. Access denied.");
      }

      if (!response.ok) {
        throw new Error(`Authentication error: HTTP ${response.status}`);
      }

      const data = await response.json();

      // Successful verification
      adminPin = pin;
      sessionStorage.setItem("baes_admin_pin", pin);

      // Transition views
      if (pinModal) pinModal.classList.add("hidden");
      if (mainDashboard) mainDashboard.classList.remove("hidden");

      allCandidates = data;
      updateMetrics();
      renderTable();
    } catch (err) {
      if (pinAlert) {
        pinAlert.textContent = err.message || "Invalid administrator PIN.";
        pinAlert.classList.remove("hidden");
      }
      if (pinInput) {
        pinInput.value = "";
        pinInput.focus();
      }
    } finally {
      setPinLoading(false);
    }
  }

  /**
   * Fetch fresh candidate records from the backend.
   */
  async function fetchDashboardData() {
    if (!adminPin) return;

    try {
      const response = await fetch(`/api/admin/dashboard?pin=${encodeURIComponent(adminPin)}`);
      if (response.status === 403) {
        lockDashboard();
        return;
      }
      if (!response.ok) throw new Error("Failed to refresh candidate records.");

      allCandidates = await response.json();
      updateMetrics();
      renderTable();
    } catch (err) {
      alert(err.message || "Error fetching dashboard records.");
    }
  }

  /**
   * Update top KPI metric cards.
   */
  function updateMetrics() {
    const total = allCandidates.length;
    const completedList = allCandidates.filter((c) => c.has_taken);
    const completedCount = completedList.length;
    const pendingCount = total - completedCount;

    let avgGpa = "0.00";
    if (completedCount > 0) {
      const sumGpa = completedList.reduce((acc, c) => acc + (parseFloat(c.gpa) || 0.0), 0);
      avgGpa = (sumGpa / completedCount).toFixed(2);
    }

    if (metricTotal) metricTotal.textContent = total;
    if (metricCompleted) metricCompleted.textContent = completedCount;
    if (metricPending) metricPending.textContent = pendingCount;
    if (metricAvgGpa) metricAvgGpa.textContent = avgGpa;
  }

  /**
   * Render candidate records table matching current search and filter criteria.
   */
  function renderTable() {
    if (!tableBody) return;
    tableBody.innerHTML = "";

    const query = (searchInput?.value || "").trim().toUpperCase();

    const filtered = allCandidates.filter((c) => {
      // 1. Status Filter
      if (currentFilter === "completed" && !c.has_taken) return false;
      if (currentFilter === "pending" && c.has_taken) return false;

      // 2. Search Query Filter
      if (query && !String(c.matric_no || "").toUpperCase().includes(query)) {
        return false;
      }

      return true;
    });

    if (filtered.length === 0) {
      if (tableEmpty) tableEmpty.classList.remove("hidden");
      return;
    }

    if (tableEmpty) tableEmpty.classList.add("hidden");

    filtered.forEach((candidate) => {
      const tr = document.createElement("tr");
      tr.className = "hover:bg-slate-50/80 transition-colors";

      const hasTaken = Boolean(candidate.has_taken);
      const scores = candidate.scores || {};

      // Requirement 3: Use text-baes-gold for "Pending" and text-green-600 for "Completed"
      const statusHtml = hasTaken
        ? `<span class="text-green-600 font-bold flex items-center space-x-1.5"><span class="w-2 h-2 rounded-full bg-green-500 inline-block"></span><span>Completed</span></span>`
        : `<span class="text-baes-gold font-bold flex items-center space-x-1.5"><span class="w-2 h-2 rounded-full bg-baes-gold inline-block"></span><span>Pending</span></span>`;

      // Format individual scores
      const phyScore = hasTaken && scores["PHY 101"] !== undefined
        ? `<span class="font-bold ${scores["PHY 101"] < 40 ? "text-baes-red" : "text-slate-800"}">${parseFloat(scores["PHY 101"]).toFixed(1)}%</span>`
        : `<span class="text-slate-300 font-normal">-</span>`;

      const chmScore = hasTaken && scores["CHM 101"] !== undefined
        ? `<span class="font-bold ${scores["CHM 101"] < 40 ? "text-baes-red" : "text-slate-800"}">${parseFloat(scores["CHM 101"]).toFixed(1)}%</span>`
        : `<span class="text-slate-300 font-normal">-</span>`;

      const mthScore = hasTaken && scores["MTH 101"] !== undefined
        ? `<span class="font-bold ${scores["MTH 101"] < 40 ? "text-baes-red" : "text-slate-800"}">${parseFloat(scores["MTH 101"]).toFixed(1)}%</span>`
        : `<span class="text-slate-300 font-normal">-</span>`;

      const gpa = hasTaken && candidate.gpa !== undefined && candidate.gpa !== null
        ? `<span class="font-black text-baes-blue text-sm">${parseFloat(candidate.gpa).toFixed(2)}</span>`
        : `<span class="text-slate-300 font-normal">-</span>`;

      // Action column: "View Answers" and "Reset" for completed exams
      const actionHtml = hasTaken
        ? `<div class="flex items-center justify-end space-x-1.5">
            <button
              type="button"
              class="btn-view-answers px-2.5 py-1.5 bg-baes-blue text-white rounded-lg text-xs font-semibold hover:bg-blue-800 transition shadow-sm"
              data-matric="${candidate.matric_no}"
              title="View Submitted Answers"
            >
              View Answers
            </button>
            <button
              type="button"
              class="btn-reset-student px-2.5 py-1.5 bg-baes-red hover:bg-red-700 text-white rounded-lg text-xs font-semibold transition shadow-sm flex items-center space-x-1"
              data-matric="${candidate.matric_no}"
              title="Reset Student Attempt"
            >
              <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
              <span>Reset</span>
            </button>
          </div>`
        : `<span class="text-slate-300 text-xs italic">N/A</span>`;

      tr.innerHTML = `
        <td class="p-4 font-mono font-bold text-slate-900">${candidate.matric_no}</td>
        <td class="p-4">${statusHtml}</td>
        <td class="p-4">${phyScore}</td>
        <td class="p-4">${chmScore}</td>
        <td class="p-4">${mthScore}</td>
        <td class="p-4">${gpa}</td>
        <td class="p-4 text-right">${actionHtml}</td>
      `;

      tableBody.appendChild(tr);
    });

    // Attach event listeners for View Answers buttons
    document.querySelectorAll(".btn-view-answers").forEach((btn) => {
      btn.addEventListener("click", () => {
        const matric = btn.getAttribute("data-matric");
        openAnswersModal(matric);
      });
    });

    // Attach event listeners for Reset Student buttons
    document.querySelectorAll(".btn-reset-student").forEach((btn) => {
      btn.addEventListener("click", async () => {
        const matric = btn.getAttribute("data-matric");
        await handleResetStudent(matric, btn);
      });
    });
  }

  /**
   * Reset candidate's exam attempt so they can re-take the CBT.
   */
  async function handleResetStudent(matricNo, btnElement = null) {
    if (!matricNo) return;

    const confirmed = window.confirm("Are you sure you want to reset this student's exam attempt?");
    if (!confirmed) return;

    if (!adminPin) {
      alert("Administrator PIN missing. Please re-authenticate.");
      return;
    }

    const origHtml = btnElement ? btnElement.innerHTML : "";
    if (btnElement) {
      btnElement.disabled = true;
      btnElement.innerHTML = `
        <svg class="animate-spin w-3.5 h-3.5 text-white" fill="none" viewBox="0 0 24 24">
          <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
          <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"></path>
        </svg>
        <span>Resetting...</span>
      `;
    }

    try {
      const url = `/api/admin/reset-student?matric_no=${encodeURIComponent(matricNo)}&pin=${encodeURIComponent(adminPin)}`;
      const response = await fetch(url, {
        method: "POST",
      });

      if (response.status === 403) {
        alert("Invalid administrator PIN or unauthorized request.");
        return;
      }

      if (!response.ok) {
        const errData = await response.json().catch(() => ({}));
        throw new Error(errData.detail || `HTTP ${response.status}`);
      }

      const res = await response.json();
      console.log("[Admin]", res.message);

      // Dynamically refresh the admin dashboard table and metrics
      await fetchDashboardData();
    } catch (err) {
      alert(err.message || "Failed to reset student exam attempt.");
      if (btnElement) {
        btnElement.disabled = false;
        btnElement.innerHTML = origHtml;
      }
    }
  }

  /**
   * Requirement 4: Implement View Answers modal logic to show student selection.
   */
  function openAnswersModal(matricNo) {
    const candidate = allCandidates.find((c) => c.matric_no === matricNo);
    if (!candidate) return;

    if (modalCandidateMatric) modalCandidateMatric.textContent = candidate.matric_no;
    if (modalGpa) modalGpa.textContent = `${parseFloat(candidate.gpa || 0).toFixed(2)} / 5.00`;

    const scores = candidate.scores || {};
    const phy = scores["PHY 101"] !== undefined ? `${scores["PHY 101"].toFixed(0)}%` : "-";
    const chm = scores["CHM 101"] !== undefined ? `${scores["CHM 101"].toFixed(0)}%` : "-";
    const mth = scores["MTH 101"] !== undefined ? `${scores["MTH 101"].toFixed(0)}%` : "-";

    if (modalScoresSummary) {
      modalScoresSummary.textContent = `${phy} / ${chm} / ${mth}`;
    }

    const submittedAnswers = candidate.submitted_answers || {};
    const answeredKeys = Object.keys(submittedAnswers);
    if (modalAnsweredCount) {
      modalAnsweredCount.textContent = `${answeredKeys.length} Question(s)`;
    }

    if (modalAnswersContainer) {
      modalAnswersContainer.innerHTML = "";

      if (answeredKeys.length === 0) {
        modalAnswersContainer.innerHTML = `
          <div class="p-6 text-center text-slate-400 text-xs font-semibold bg-slate-50 rounded-xl border border-slate-200">
            No submitted answers recorded for this candidate.
          </div>
        `;
      } else {
        answeredKeys.forEach((qId, idx) => {
          const selectedOptionIndex = submittedAnswers[qId];
          const questionMeta = questionsMap[qId];
          const course = questionMeta?.course || "Course";
          const questionText = questionMeta?.question || `Question ID: ${qId}`;

          let selectedText = "";
          let letter = OPTION_LETTERS[selectedOptionIndex] || `Index ${selectedOptionIndex}`;

          if (questionMeta && questionMeta.options && questionMeta.options[selectedOptionIndex]) {
            selectedText = questionMeta.options[selectedOptionIndex];
          }

          const card = document.createElement("div");
          card.className = "p-3.5 bg-slate-50 border border-slate-200 rounded-xl text-xs space-y-1.5";
          card.innerHTML = `
            <div class="flex items-center justify-between">
              <span class="font-bold text-slate-700 uppercase tracking-wide">Q${idx + 1} • <span class="text-baes-blue font-extrabold">${course}</span></span>
              <span class="px-2 py-0.5 rounded bg-blue-100 text-baes-blue font-mono font-bold text-[11px]">Selected: Option ${letter}</span>
            </div>
            <p class="text-slate-800 font-medium leading-relaxed">${questionText}</p>
            ${selectedText ? `<p class="text-slate-500 italic bg-white p-2 rounded-lg border border-slate-200">Choice: "${selectedText}"</p>` : ""}
          `;
          modalAnswersContainer.appendChild(card);
        });
      }
    }

    if (answersModal) answersModal.classList.remove("hidden");
  }

  function closeAnswersModal() {
    if (answersModal) answersModal.classList.add("hidden");
  }

  /**
   * Requirement 5: Implement Export CSV button to trigger download from /api/admin/export?pin=...
   */
  function exportCsv() {
    if (!adminPin) {
      alert("Administrator PIN missing. Please re-authenticate.");
      return;
    }
    const exportUrl = `/api/admin/export?pin=${encodeURIComponent(adminPin)}`;
    window.location.href = exportUrl;
  }

  /**
   * Re-lock the admin panel and clear session credentials.
   */
  function lockDashboard() {
    adminPin = "";
    sessionStorage.removeItem("baes_admin_pin");
    allCandidates = [];
    if (mainDashboard) mainDashboard.classList.add("hidden");
    if (pinModal) pinModal.classList.remove("hidden");
    if (pinInput) {
      pinInput.value = "";
      pinInput.focus();
    }
  }

  // Event Listeners Initialization
  document.addEventListener("DOMContentLoaded", () => {
    loadQuestionMeta();

    // Auto-authenticate if PIN is stored in session
    if (adminPin) {
      authenticatePin(adminPin);
    }

    // PIN Form Submission
    if (pinForm) {
      pinForm.addEventListener("submit", (e) => {
        e.preventDefault();
        const pin = (pinInput?.value || "").trim();
        if (pin) {
          authenticatePin(pin);
        }
      });
    }

    // Export CSV
    if (btnExportCsv) {
      btnExportCsv.addEventListener("click", exportCsv);
    }

    // Refresh Data
    if (btnRefresh) {
      btnRefresh.addEventListener("click", fetchDashboardData);
    }

    // Lock Dashboard
    if (btnLock) {
      btnLock.addEventListener("click", lockDashboard);
    }

    // Close Answers Modal
    if (btnCloseAnswers) btnCloseAnswers.addEventListener("click", closeAnswersModal);
    if (btnCloseAnswersFooter) btnCloseAnswersFooter.addEventListener("click", closeAnswersModal);

    if (answersModal) {
      answersModal.addEventListener("click", (e) => {
        if (e.target === answersModal) closeAnswersModal();
      });
    }

    // Search Input
    if (searchInput) {
      searchInput.addEventListener("input", () => {
        renderTable();
      });
    }

    // Filter Buttons
    filterBtns.forEach((btn) => {
      btn.addEventListener("click", () => {
        filterBtns.forEach((b) => {
          b.className = "filter-btn px-3 py-1.5 rounded-lg text-xs font-bold bg-slate-100 text-slate-600 hover:bg-slate-200 transition";
        });
        btn.className = "filter-btn px-3 py-1.5 rounded-lg text-xs font-bold bg-slate-800 text-white transition";
        currentFilter = btn.getAttribute("data-filter") || "all";
        renderTable();
      });
    });
  });
})();
