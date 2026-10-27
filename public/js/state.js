/**
 * state.js - Central State Management & localStorage Synchronization
 * Preserves candidate answers, active session, and exam progress across refreshes.
 * Implements per-student namespacing and clean state reset utilities.
 */

const STORAGE_KEYS = {
  STUDENT: "cbt_student_session",
  ANSWERS: "cbt_exam_answers",
  QUESTIONS: "cbt_exam_questions",
  ACTIVE_COURSE: "cbt_active_course",
  ACTIVE_INDEX: "cbt_active_index",
  TIMER_END: "cbt_timer_end_time",
  RESULTS: "cbt_submission_results",
  EXAM_STATE: "cbt_exam_state",
};

const State = {
  // ================= SESSION MANAGEMENT =================
  setSession(studentData) {
    localStorage.setItem(STORAGE_KEYS.STUDENT, JSON.stringify(studentData));
  },

  getSession() {
    const raw = localStorage.getItem(STORAGE_KEYS.STUDENT);
    try {
      return raw ? JSON.parse(raw) : null;
    } catch {
      return null;
    }
  },

  getMatricNo() {
    const session = this.getSession();
    return (session?.matric_no || session?.student?.matric_no || "").trim().toUpperCase();
  },

  // ================= NAMESPACED STORAGE KEYS =================
  getAnswersKey(matricNo) {
    const m = (matricNo || this.getMatricNo()).trim().toUpperCase();
    return m ? `cbt_answers_${m}` : STORAGE_KEYS.ANSWERS;
  },

  // ================= QUESTIONS STATE =================
  setQuestions(questions) {
    localStorage.setItem(STORAGE_KEYS.QUESTIONS, JSON.stringify(questions));
  },

  getQuestions() {
    const raw = localStorage.getItem(STORAGE_KEYS.QUESTIONS);
    try {
      return raw ? JSON.parse(raw) : [];
    } catch {
      return [];
    }
  },

  // ================= ANSWERS AUTO-SAVE (NAMESPACED) =================
  getAnswers(matricNo) {
    const key = this.getAnswersKey(matricNo);
    const raw = localStorage.getItem(key);
    try {
      if (raw) return JSON.parse(raw);
    } catch {}

    // Fallback to check generic legacy key if namespaced key is empty
    if (key !== STORAGE_KEYS.ANSWERS) {
      const legacyRaw = localStorage.getItem(STORAGE_KEYS.ANSWERS);
      try {
        if (legacyRaw) return JSON.parse(legacyRaw);
      } catch {}
    }
    return {};
  },

  saveAnswer(questionId, optionIndex, matricNo) {
    const key = this.getAnswersKey(matricNo);
    const answers = this.getAnswers(matricNo);
    if (optionIndex === null || optionIndex === undefined) {
      delete answers[questionId];
    } else {
      answers[questionId] = parseInt(optionIndex, 10);
    }
    localStorage.setItem(key, JSON.stringify(answers));
    return answers;
  },

  getAnswer(questionId, matricNo) {
    const answers = this.getAnswers(matricNo);
    return answers[questionId] !== undefined ? answers[questionId] : null;
  },

  hasAnswer(questionId, matricNo) {
    const answers = this.getAnswers(matricNo);
    return answers[questionId] !== undefined && answers[questionId] !== null;
  },

  // ================= ACTIVE NAVIGATION =================
  setActiveCourse(courseCode) {
    localStorage.setItem(STORAGE_KEYS.ACTIVE_COURSE, courseCode);
  },

  getActiveCourse() {
    return localStorage.getItem(STORAGE_KEYS.ACTIVE_COURSE) || "PHY 101";
  },

  setActiveIndex(index) {
    localStorage.setItem(STORAGE_KEYS.ACTIVE_INDEX, index.toString());
  },

  getActiveIndex() {
    const val = localStorage.getItem(STORAGE_KEYS.ACTIVE_INDEX);
    return val !== null ? parseInt(val, 10) : 0;
  },

  // ================= TIMER TIMESTAMP =================
  setTimerEnd(endTimeMs) {
    localStorage.setItem(STORAGE_KEYS.TIMER_END, endTimeMs.toString());
  },

  getTimerEnd() {
    const raw = localStorage.getItem(STORAGE_KEYS.TIMER_END);
    return raw ? parseInt(raw, 10) : null;
  },

  // ================= SUBMISSION PAYLOAD & RESULTS =================
  buildSubmitPayload() {
    const matricNo = this.getMatricNo();
    return {
      matric_no: matricNo,
      answers: this.getAnswers(matricNo),
    };
  },

  saveResults(resultsData) {
    localStorage.setItem(STORAGE_KEYS.RESULTS, JSON.stringify(resultsData));
  },

  getResults() {
    const raw = localStorage.getItem(STORAGE_KEYS.RESULTS);
    try {
      return raw ? JSON.parse(raw) : null;
    } catch {
      return null;
    }
  },

  // ================= CLEAN RESET UTILITIES =================
  /**
   * Reset exam-in-progress state (questions, answers, timers, navigation).
   * Prevents stale choices from lingering across student logins.
   * @param {string} [matricNo]
   */
  clearExamState(matricNo) {
    const targetMatric = (matricNo || this.getMatricNo()).trim().toUpperCase();

    // 1. Remove generic / legacy answer keys
    localStorage.removeItem(STORAGE_KEYS.ANSWERS);
    localStorage.removeItem("cbt_answers");
    localStorage.removeItem("cbt_exam_answers");

    // 2. Remove namespaced answer keys
    if (targetMatric) {
      localStorage.removeItem(`cbt_answers_${targetMatric}`);
    }
    // Scan and clean any remaining cbt_answers_* keys
    try {
      for (let i = localStorage.length - 1; i >= 0; i--) {
        const k = localStorage.key(i);
        if (k && (k.startsWith("cbt_answers") || k.startsWith("cbt_exam_answers"))) {
          localStorage.removeItem(k);
        }
      }
    } catch {}

    // 3. Clear cached questions
    localStorage.removeItem(STORAGE_KEYS.QUESTIONS);
    localStorage.removeItem("cbt_questions");
    localStorage.removeItem("cbt_exam_questions");

    // 4. Clear active navigation and exam progression
    localStorage.removeItem(STORAGE_KEYS.ACTIVE_COURSE);
    localStorage.removeItem(STORAGE_KEYS.ACTIVE_INDEX);
    localStorage.removeItem(STORAGE_KEYS.EXAM_STATE);
    localStorage.removeItem("cbt_active_course");
    localStorage.removeItem("cbt_active_index");
    localStorage.removeItem("cbt_exam_state");

    // 5. Clear timer timestamps
    localStorage.removeItem(STORAGE_KEYS.TIMER_END);
    localStorage.removeItem("cbt_timer_end_time");

    // Reset timer instance if active
    if (window.CBT_Timer && typeof window.CBT_Timer.reset === "function") {
      window.CBT_Timer.reset();
    }
  },

  /**
   * Full session reset on candidate logout.
   */
  clearSession() {
    this.clearExamState();
    localStorage.removeItem(STORAGE_KEYS.STUDENT);
    localStorage.removeItem(STORAGE_KEYS.RESULTS);
    localStorage.removeItem("cbt_student_session");
    localStorage.removeItem("cbt_submission_results");
  },
};

// Export to global scope
window.CBT_State = State;
