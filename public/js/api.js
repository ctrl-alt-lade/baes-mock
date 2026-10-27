/**
 * api.js - Backend communication layer for CBT Web App.
 * Uses relative API_BASE path to run seamlessly on the same host and port as FastAPI.
 */

const API_BASE = "/api";

const API = {
  /**
   * Authenticate student by matriculation number.
   * @param {string} matricNo
   * @returns {Promise<Object>}
   */
  async login(matricNo) {
    try {
      const response = await fetch(`${API_BASE}/login`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ matric_no: matricNo.trim() }),
      });

      const data = await response.json();

      if (!response.ok) {
        const errorMsg = data.detail || "Authentication failed. Please try again.";
        const error = new Error(errorMsg);
        error.status = response.status;
        throw error;
      }

      return data;
    } catch (err) {
      if (err.status) throw err;
      throw new Error("Unable to connect to the CBT server. Please verify backend is running.");
    }
  },

  /**
   * Fetch questions randomized for the active student with answer keys stripped out.
   * @param {string} [matricNo]
   * @returns {Promise<Array>}
   */
  async fetchQuestions(matricNo) {
    try {
      if (!matricNo) {
        // Retrieve matric_no from localStorage (cbt_student_session)
        const session = window.CBT_State ? window.CBT_State.getSession() : null;
        if (session && session.matric_no) {
          matricNo = session.matric_no;
        } else {
          try {
            const raw = localStorage.getItem("cbt_student_session");
            const parsed = raw ? JSON.parse(raw) : null;
            matricNo = parsed?.matric_no || "";
          } catch {
            matricNo = "";
          }
        }
      }

      const url = matricNo
        ? `${API_BASE}/questions?matric_no=${encodeURIComponent(matricNo.trim())}`
        : `${API_BASE}/questions`;

      const response = await fetch(url, {
        method: "GET",
        headers: {
          "Content-Type": "application/json",
        },
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "Failed to fetch exam questions.");
      }

      // Backend returns { status: "success", total: N, questions: [...] }
      if (Array.isArray(data.questions)) {
        return data.questions;
      } else if (Array.isArray(data)) {
        return data;
      }
      return [];
    } catch (err) {
      console.error("[API Error] fetchQuestions:", err);
      throw err;
    }
  },

  /**
   * Submit student answers for grading and GPA computation.
   * @param {Object} payload { matric_no: string, answers: { [qId]: optionIndex } }
   * @returns {Promise<Object>}
   */
  async submitExam(payload) {
    try {
      const response = await fetch(`${API_BASE}/submit`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(payload),
      });

      const data = await response.json();

      if (!response.ok) {
        const errorMsg = data.detail || "Failed to submit examination.";
        const error = new Error(errorMsg);
        error.status = response.status;
        throw error;
      }

      return data;
    } catch (err) {
      console.error("[API Error] submitExam:", err);
      throw err;
    }
  },
};

// Export to global scope
window.CBT_API = API;
