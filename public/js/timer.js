/**
 * timer.js - Persistent countdown timer and auto-submission trigger.
 * Storing the absolute target end-time in localStorage guarantees
 * page reloads never reset the candidate's remaining time.
 * Upgraded with BAES Brand Guide: switches to 'text-baes-red font-bold' when <= 5 mins remain.
 */

const Timer = {
  durationSeconds: 60 * 60, // 60 minutes default
  intervalId: null,
  onExpireCallback: null,

  /**
   * Start or resume the countdown timer.
   * @param {HTMLElement} displayElement
   * @param {Function} onExpire
   */
  start(displayElement, onExpire) {
    this.onExpireCallback = onExpire;
    let endTime = window.CBT_State.getTimerEnd();

    // If no existing timer session, initialize end timestamp
    if (!endTime) {
      endTime = Date.now() + this.durationSeconds * 1000;
      window.CBT_State.setTimerEnd(endTime);
    }

    const updateClock = () => {
      const now = Date.now();
      const remainingMs = endTime - now;
      const remainingSeconds = Math.max(0, Math.floor(remainingMs / 1000));

      const minutes = Math.floor(remainingSeconds / 60);
      const seconds = remainingSeconds % 60;
      const formatted = `${String(minutes).padStart(2, "0")}:${String(seconds).padStart(2, "0")}`;

      if (displayElement) {
        displayElement.textContent = formatted;

        // Visual warning when 5 minutes or less remain (300 seconds)
        if (remainingSeconds <= 300) {
          displayElement.classList.add("text-baes-red", "font-bold", "animate-pulse");
          displayElement.classList.remove("text-slate-800");
          const container = displayElement.closest("#timer-badge");
          if (container) {
            container.classList.add("border-baes-red", "bg-red-50/70");
            container.classList.remove("border-slate-200", "bg-slate-50");
          }
        }
      }

      // Time expired
      if (remainingSeconds <= 0) {
        this.stop();
        if (typeof this.onExpireCallback === "function") {
          this.onExpireCallback();
        }
      }
    };

    // Run immediate tick and start interval
    updateClock();
    this.intervalId = setInterval(updateClock, 1000);
  },

  /**
   * Stop the running countdown interval.
   */
  stop() {
    if (this.intervalId) {
      clearInterval(this.intervalId);
      this.intervalId = null;
    }
  },

  /**
   * Clean up timer timestamp from localStorage upon successful submission.
   */
  reset() {
    this.stop();
    localStorage.removeItem("cbt_timer_end_time");
  },
};

// Export to global scope
window.CBT_Timer = Timer;
