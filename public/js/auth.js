/**
 * auth.js - Authentication & Fresh Session Initialization
 * Handles student login and resets stale cached questions, answers, and timers
 * when a new matriculation number is authenticated.
 */

const Auth = {
  /**
   * Authenticate student and enforce a clean exam state for new matric numbers.
   * @param {string} matricNo
   * @returns {Promise<Object>} studentSession
   */
  async handleLogin(matricNo) {
    const cleanMatric = matricNo.trim().toUpperCase();

    // 1. Check if the stored session's matric_no differs from the current login
    const prevSession = window.CBT_State ? window.CBT_State.getSession() : null;
    const prevMatric = (prevSession?.matric_no || prevSession?.student?.matric_no || "").trim().toUpperCase();

    // 2. If a new matric number logs in (or switching accounts), clear stale state
    if (!prevMatric || prevMatric !== cleanMatric) {
      if (window.CBT_State) {
        window.CBT_State.clearExamState(prevMatric || cleanMatric);
      }
    }

    // 3. Authenticate with backend API
    const response = await window.CBT_API.login(cleanMatric);
    const studentSession = response.student || { matric_no: cleanMatric };

    // 4. Save new active session
    if (window.CBT_State) {
      window.CBT_State.setSession(studentSession);
    }

    return studentSession;
  },

  /**
   * Bind event listeners to login form on index.html.
   */
  init() {
    const form = document.getElementById("login-form");
    if (!form) return;

    const matricInput = document.getElementById("matric-input");
    const loginBtn = document.getElementById("login-btn");
    const btnText = document.getElementById("btn-text");
    const btnSpinner = document.getElementById("btn-spinner");
    const alertBox = document.getElementById("login-alert");
    const alertMsg = document.getElementById("login-alert-msg");

    function showAlert(msg, isError = true) {
      if (!alertBox || !alertMsg) return;
      alertMsg.textContent = msg;
      alertBox.className = isError
        ? "mb-6 p-4 rounded-xl border text-sm flex items-start space-x-3 bg-red-50 border-red-200 text-baes-red font-medium"
        : "mb-6 p-4 rounded-xl border text-sm flex items-start space-x-3 bg-emerald-50 border-emerald-200 text-emerald-700 font-medium";
      alertBox.classList.remove("hidden");
    }

    function setLoading(isLoading) {
      if (!loginBtn) return;
      loginBtn.disabled = isLoading;
      if (isLoading) {
        if (btnText) btnText.textContent = "Verifying Credentials...";
        if (btnSpinner) btnSpinner.classList.remove("hidden");
      } else {
        if (btnText) btnText.textContent = "Authenticate & Begin Exam";
        if (btnSpinner) btnSpinner.classList.add("hidden");
      }
    }

    form.addEventListener("submit", async (e) => {
      e.preventDefault();
      if (alertBox) alertBox.classList.add("hidden");
      const matricNo = matricInput?.value?.trim() || "";

      if (!matricNo) {
        showAlert("Please enter your matriculation number.");
        return;
      }

      setLoading(true);

      try {
        await this.handleLogin(matricNo);
        // Redirect to examination progress screen
        window.location.href = "exam.html";
      } catch (err) {
        setLoading(false);
        showAlert(err.message || "Failed to log in.");
      }
    });
  },
};

// Export to global scope
window.CBT_Auth = Auth;

// Auto-initialize when loaded on login page
document.addEventListener("DOMContentLoaded", () => {
  Auth.init();
});
