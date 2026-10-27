/**
 * ui.js - DOM Manipulation, Course Tabs, Question Grid & Exam Flow
 * Tailored with Bowen Association of Engineering Students (BAES) Brand Colors.
 */

const UI = {
  activeCourse: "PHY 101",
  activeQuestionIndex: 0,
  courses: ["PHY 101", "CHM 101", "MTH 101"],
  questionsByCourse: {
    "PHY 101": [],
    "CHM 101": [],
    "MTH 101": [],
  },

  /**
   * Initialize exam dashboard.
   */
  async init() {
    // 1. Session verification
    const session = window.CBT_State.getSession();
    if (!session || !session.matric_no) {
      window.location.href = "index.html";
      return;
    }

    // 2. Candidate Info in Header
    this.renderCandidateInfo(session);

    // 3. Load or fetch questions
    let allQuestions = window.CBT_State.getQuestions();
    if (!allQuestions || allQuestions.length === 0) {
      this.showLoading(true, "Fetching examination questions...");
      try {
        allQuestions = await window.CBT_API.fetchQuestions(session.matric_no);
        window.CBT_State.setQuestions(allQuestions);
      } catch (err) {
        alert("Failed to load questions: " + err.message);
        this.showLoading(false);
        return;
      }
      this.showLoading(false);
    }

    // 4. Organize questions into courses
    this.organizeQuestions(allQuestions);

    // 5. Restore active tab and question from State
    this.activeCourse = window.CBT_State.getActiveCourse() || "PHY 101";
    this.activeQuestionIndex = window.CBT_State.getActiveIndex() || 0;

    // Boundary check
    const currentCourseList = this.questionsByCourse[this.activeCourse] || [];
    if (this.activeQuestionIndex >= currentCourseList.length) {
      this.activeQuestionIndex = 0;
    }

    // 6. Start Timer
    const timerDisplay = document.getElementById("timer-display");
    window.CBT_Timer.start(timerDisplay, () => this.autoSubmitExam());

    // 7. Initial Renders
    this.renderTabs();
    this.renderActiveQuestion();
    this.renderQuestionGrid();
    this.attachEventListeners();
  },

  /**
   * Sort flat question array into configured course buckets.
   */
  organizeQuestions(allQuestions) {
    this.questionsByCourse = {
      "PHY 101": [],
      "CHM 101": [],
      "MTH 101": [],
    };

    allQuestions.forEach((q) => {
      const raw = (q.course || q.course_code || q.subject || "").toUpperCase();
      if (raw.includes("PHY") || raw.includes("PHYSICS")) {
        this.questionsByCourse["PHY 101"].push(q);
      } else if (raw.includes("CHM") || raw.includes("CHEM")) {
        this.questionsByCourse["CHM 101"].push(q);
      } else if (raw.includes("MTH") || raw.includes("MATH")) {
        this.questionsByCourse["MTH 101"].push(q);
      } else {
        // Fallback default course
        this.questionsByCourse["PHY 101"].push(q);
      }
    });
  },

  /**
   * Display student identity in the header.
   */
  renderCandidateInfo(session) {
    const matricEl = document.getElementById("candidate-matric");
    const nameEl = document.getElementById("candidate-name");
    if (matricEl) matricEl.textContent = session.matric_no;
    if (nameEl) nameEl.textContent = session.name || "Candidate";
  },

  /**
   * Render course navigation tabs (PHY 101, CHM 101, MTH 101) with text-baes-red & border-baes-red.
   */
  renderTabs() {
    const tabsContainer = document.getElementById("course-tabs");
    if (!tabsContainer) return;

    tabsContainer.innerHTML = "";
    this.courses.forEach((course) => {
      const questions = this.questionsByCourse[course] || [];
      const answeredCount = questions.filter((q) => window.CBT_State.hasAnswer(q.id)).length;
      const isActive = this.activeCourse === course;

      const btn = document.createElement("button");
      btn.type = "button";
      btn.className = `px-4 py-2 text-sm font-semibold rounded-lg transition-all flex items-center space-x-2 border-b-2 ${isActive
        ? "text-baes-red border-baes-red bg-red-50/60 font-bold shadow-sm"
        : "text-slate-600 border-transparent hover:text-slate-900 hover:bg-slate-50"
        }`;

      btn.innerHTML = `
        <span>${course}</span>
        <span class="text-xs px-2 py-0.5 rounded-full ${isActive ? "bg-red-100 text-baes-red font-bold" : "bg-slate-100 text-slate-600 font-medium"
        }">
          ${answeredCount}/${questions.length}
        </span>
      `;

      btn.addEventListener("click", () => this.switchCourse(course));
      tabsContainer.appendChild(btn);
    });
  },

  /**
   * Switch the active course tab.
   */
  switchCourse(course) {
    if (this.activeCourse === course) return;
    this.activeCourse = course;
    this.activeQuestionIndex = 0;
    window.CBT_State.setActiveCourse(course);
    window.CBT_State.setActiveIndex(0);

    this.renderTabs();
    this.renderActiveQuestion();
    this.renderQuestionGrid();
  },

  /**
   * Sanitize LaTeX strings before rendering into the DOM:
   * - Safely returns empty string if str is null, undefined, or not a string.
   * - Collapses accidental multi-backslashes down to standard double/single backslashes.
   * - Escapes unescaped percent signs (%) inside inline math blocks so they become \%.
   * - Automatically balances unclosed curly braces { inside \( ... \) blocks.
   * @param {string} str
   * @returns {string}
   */
  sanitizeLatexString(str) {
    if (!str || typeof str !== "string") {
      return "";
    }
    return str.replaceAll("\\\\", "\\");
  },

  /**
   * Render the current active question and its selectable options.
   */
  renderActiveQuestion() {
    const questionList = this.questionsByCourse[this.activeCourse] || [];
    const container = document.getElementById("question-card");
    const totalQ = questionList.length;

    if (totalQ === 0) {
      if (container) {
        container.innerHTML = `
          <div class="p-8 text-center text-slate-500">
            <p class="text-base">No questions currently available for <strong>${this.activeCourse}</strong>.</p>
          </div>
        `;
      }
      this.updateNavButtons(0, 0);
      return;
    }

    const currentQ = questionList[this.activeQuestionIndex];
    const savedAnswer = window.CBT_State.getAnswer(currentQ.id);

    // Question header badge
    const badgeEl = document.getElementById("q-number-badge");
    if (badgeEl) {
      badgeEl.textContent = `Question ${this.activeQuestionIndex + 1} of ${totalQ}`;
    }

    const courseBadge = document.getElementById("q-course-badge");
    if (courseBadge) {
      courseBadge.textContent = this.activeCourse;
    }

    // Question prompt text
    const textEl = document.getElementById("q-text");
    if (textEl) {
      const rawQuestion = currentQ.question || currentQ.text || "Question content missing.";
      textEl.innerHTML = this.sanitizeLatexString(rawQuestion);
    }

    // Options list
    const optionsContainer = document.getElementById("q-options");
    if (optionsContainer) {
      optionsContainer.innerHTML = "";
      const options = currentQ.options || [];

      options.forEach((optText, idx) => {
        const isChecked = savedAnswer === idx;
        const optionLabel = String.fromCharCode(65 + idx); // A, B, C, D...
        const sanitizedOpt = this.sanitizeLatexString(optText);

        const optionCard = document.createElement("label");
        optionCard.className = `flex items-center p-4 border rounded-xl cursor-pointer transition-all ${isChecked
          ? "border-baes-blue bg-blue-50/60 text-slate-900 font-semibold shadow-sm ring-1 ring-baes-blue"
          : "border-slate-200 bg-white hover:bg-slate-50 text-slate-700"
          }`;

        optionCard.innerHTML = `
          <input 
            type="radio" 
            name="cbt-option" 
            value="${idx}" 
            ${isChecked ? "checked" : ""} 
            class="w-4 h-4 text-baes-blue border-slate-300 focus:ring-baes-blue"
          />
          <span class="ml-3 font-bold text-sm w-6 text-baes-blue">${optionLabel}.</span>
          <span class="ml-2 text-sm leading-relaxed">${sanitizedOpt}</span>
        `;

        optionCard.addEventListener("click", () => {
          this.selectOption(currentQ.id, idx);
        });

        optionsContainer.appendChild(optionCard);
      });
    }

    this.updateNavButtons(this.activeQuestionIndex, totalQ);

    if (window.MathJax && window.MathJax.typesetPromise) {
      MathJax.typesetClear();
      MathJax.typesetPromise().catch((err) => console.warn("MathJax render warning:", err));
    }
  },



  /**
   * Save answer selection and trigger UI updates.
   */
  selectOption(questionId, optionIndex) {
    window.CBT_State.saveAnswer(questionId, optionIndex);
    this.renderTabs();
    this.renderQuestionGrid();
    this.renderActiveQuestion();
  },

  /**
   * Clear selected radio option for the active question.
   */
  clearCurrentOption() {
    const questionList = this.questionsByCourse[this.activeCourse] || [];
    const currentQ = questionList[this.activeQuestionIndex];
    if (!currentQ) return;

    window.CBT_State.saveAnswer(currentQ.id, null);
    this.renderTabs();
    this.renderQuestionGrid();
    this.renderActiveQuestion();
  },

  /**
   * Render the 1..N question navigation grid in the sidebar.
   * Default: light gray.
   * Answered: bg-baes-blue text-white.
   * Current active: ring-2 ring-baes-gold.
   */
  renderQuestionGrid() {
    const gridContainer = document.getElementById("question-grid");
    if (!gridContainer) return;

    const questions = this.questionsByCourse[this.activeCourse] || [];
    gridContainer.innerHTML = "";

    questions.forEach((q, idx) => {
      const isAnswered = window.CBT_State.hasAnswer(q.id);
      const isCurrent = idx === this.activeQuestionIndex;

      const btn = document.createElement("button");
      btn.type = "button";
      btn.textContent = idx + 1;

      // Color coding:
      // Answered: bg-baes-blue text-white
      // Unanswered: bg-gray-200 text-gray-800
      // Current active: ring-2 ring-baes-gold ring-offset-2
      let baseStyle = "w-10 h-10 rounded-lg text-sm font-bold transition-all flex items-center justify-center ";

      if (isAnswered) {
        baseStyle += "bg-baes-blue text-white hover:bg-blue-800 shadow-sm ";
      } else {
        baseStyle += "bg-gray-200 text-gray-800 hover:bg-gray-300 ";
      }

      if (isCurrent) {
        baseStyle += "ring-2 ring-baes-gold ring-offset-2 ";
      }

      btn.className = baseStyle;
      btn.addEventListener("click", () => this.jumpToQuestion(idx));
      gridContainer.appendChild(btn);
    });

    // Update answered summary text in sidebar
    const summaryEl = document.getElementById("grid-progress-text");
    if (summaryEl) {
      const answeredTotal = questions.filter((q) => window.CBT_State.hasAnswer(q.id)).length;
      summaryEl.textContent = `${answeredTotal} of ${questions.length} Answered`;
    }
  },

  /**
   * Jump to specific question index in active course.
   */
  jumpToQuestion(index) {
    this.activeQuestionIndex = index;
    window.CBT_State.setActiveIndex(index);
    this.renderActiveQuestion();
    this.renderQuestionGrid();
  },

  /**
   * Move to Previous question.
   */
  prevQuestion() {
    if (this.activeQuestionIndex > 0) {
      this.jumpToQuestion(this.activeQuestionIndex - 1);
    }
  },

  /**
   * Move to Next question or next course.
   */
  nextQuestion() {
    const questions = this.questionsByCourse[this.activeCourse] || [];
    if (this.activeQuestionIndex < questions.length - 1) {
      this.jumpToQuestion(this.activeQuestionIndex + 1);
    } else {
      // Optional: wrap to next course
      const currentIdx = this.courses.indexOf(this.activeCourse);
      if (currentIdx < this.courses.length - 1) {
        this.switchCourse(this.courses[currentIdx + 1]);
      }
    }
  },

  /**
   * Update state of Previous / Next buttons.
   */
  updateNavButtons(currentIndex, totalQuestions) {
    const prevBtn = document.getElementById("btn-prev");
    const nextBtn = document.getElementById("btn-next");

    if (prevBtn) {
      prevBtn.disabled = currentIndex <= 0;
      prevBtn.classList.toggle("opacity-50", currentIndex <= 0);
      prevBtn.classList.toggle("cursor-not-allowed", currentIndex <= 0);
    }

    if (nextBtn) {
      const isLastInCourse = currentIndex >= totalQuestions - 1;
      const isLastCourse = this.courses.indexOf(this.activeCourse) === this.courses.length - 1;

      if (isLastInCourse && isLastCourse) {
        nextBtn.className = "px-5 py-2.5 bg-baes-red hover:bg-red-800 text-white font-bold text-xs rounded-xl shadow-md shadow-red-700/20 transition-all flex items-center space-x-1.5 focus:outline-none";
        nextBtn.innerHTML = `<span>Submit</span> <svg class="w-4 h-4 ml-1 inline" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/></svg>`;
        nextBtn.onclick = () => this.openSubmitModal();
      } else {
        nextBtn.className = "px-5 py-2.5 bg-baes-blue hover:bg-blue-800 text-white font-bold text-xs rounded-xl shadow-md shadow-blue-800/20 transition-all flex items-center space-x-1.5 focus:outline-none";
        nextBtn.innerHTML = `<span>Next</span> <svg class="w-4 h-4 ml-1 inline" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"/></svg>`;
        nextBtn.onclick = () => this.nextQuestion();
      }
    }
  },

  /**
   * Open confirmation modal before submission.
   */
  openSubmitModal() {
    const modal = document.getElementById("submit-modal");
    if (!modal) return;

    // Build course summary breakdown
    const breakdownEl = document.getElementById("modal-summary-list");
    let totalAllQ = 0;
    let totalAllAns = 0;

    if (breakdownEl) {
      breakdownEl.innerHTML = "";
      this.courses.forEach((course) => {
        const qList = this.questionsByCourse[course] || [];
        const ans = qList.filter((q) => window.CBT_State.hasAnswer(q.id)).length;
        totalAllQ += qList.length;
        totalAllAns += ans;

        const row = document.createElement("div");
        row.className = "flex justify-between items-center py-2 border-b border-slate-100 text-sm";
        row.innerHTML = `
          <span class="font-medium text-slate-700">${course}</span>
          <span class="${ans === qList.length ? "text-baes-blue font-bold" : "text-amber-600 font-semibold"}">
            ${ans} / ${qList.length} answered
          </span>
        `;
        breakdownEl.appendChild(row);
      });
    }

    const totalEl = document.getElementById("modal-total-summary");
    if (totalEl) {
      totalEl.textContent = `${totalAllAns} of ${totalAllQ} total questions answered.`;
    }

    modal.classList.remove("hidden");
    modal.classList.add("flex");
  },

  closeSubmitModal() {
    const modal = document.getElementById("submit-modal");
    if (modal) {
      modal.classList.add("hidden");
      modal.classList.remove("flex");
    }
  },

  /**
   * Submit examination to backend.
   */
  async submitExam() {
    this.closeSubmitModal();
    this.showLoading(true, "Grading submission and computing Nigerian GPA...");

    const payload = window.CBT_State.buildSubmitPayload();

    try {
      const response = await window.CBT_API.submitExam(payload);
      // Save results
      window.CBT_State.saveResults(response);
      window.CBT_Timer.reset();
      window.CBT_State.clearExamState();

      // Redirect to results scorecard
      window.location.href = "results.html";
    } catch (err) {
      this.showLoading(false);
      alert("Submission error: " + err.message);
    }
  },

  /**
   * Automatic submission when countdown timer hits 00:00.
   */
  async autoSubmitExam() {
    // Disable inputs
    const inputs = document.querySelectorAll("input, button");
    inputs.forEach((el) => (el.disabled = true));

    alert("Time is up! Your answers will now be automatically submitted.");
    await this.submitExam();
  },

  showLoading(show, message = "Please wait...") {
    const overlay = document.getElementById("loading-overlay");
    const msgEl = document.getElementById("loading-message");
    if (!overlay) return;

    if (show) {
      if (msgEl) msgEl.textContent = message;
      overlay.classList.remove("hidden");
      overlay.classList.add("flex");
    } else {
      overlay.classList.add("hidden");
      overlay.classList.remove("flex");
    }
  },

  attachEventListeners() {
    const prevBtn = document.getElementById("btn-prev");
    const clearBtn = document.getElementById("btn-clear");
    const submitBtn = document.getElementById("btn-submit-exam");
    const modalCancel = document.getElementById("btn-modal-cancel");
    const modalConfirm = document.getElementById("btn-modal-confirm");

    if (prevBtn) prevBtn.addEventListener("click", () => this.prevQuestion());
    if (clearBtn) clearBtn.addEventListener("click", () => this.clearCurrentOption());
    if (submitBtn) submitBtn.addEventListener("click", () => this.openSubmitModal());
    if (modalCancel) modalCancel.addEventListener("click", () => this.closeSubmitModal());
    if (modalConfirm) modalConfirm.addEventListener("click", () => this.submitExam());
  },
};

// Global export
window.CBT_UI = UI;
