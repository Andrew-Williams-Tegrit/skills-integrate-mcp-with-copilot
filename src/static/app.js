document.addEventListener("DOMContentLoaded", () => {
  const activitiesList = document.getElementById("activities-list");
  const activitySelect = document.getElementById("activity");
  const signupForm = document.getElementById("signup-form");
  const messageDiv = document.getElementById("message");

  // Attendance UI elements
  const attendanceActivitySelect = document.getElementById("attendance-activity");
  const attendanceDateInput = document.getElementById("attendance-date");
  const attendanceChecklist = document.getElementById("attendance-checklist");
  const submitAttendanceBtn = document.getElementById("submit-attendance");
  const attendanceMessageDiv = document.getElementById("attendance-message");
  const attendanceReportContainer = document.getElementById("attendance-report-container");
  const attendanceReport = document.getElementById("attendance-report");

  // Set default date to today
  attendanceDateInput.value = new Date().toISOString().split("T")[0];

  // Function to fetch activities from API
  async function fetchActivities() {
    try {
      const response = await fetch("/activities");
      const activities = await response.json();

      // Clear loading message
      activitiesList.innerHTML = "";

      // Populate activities list
      Object.entries(activities).forEach(([name, details]) => {
        const activityCard = document.createElement("div");
        activityCard.className = "activity-card";

        const spotsLeft =
          details.max_participants - details.participants.length;

        // Create participants HTML with delete icons instead of bullet points
        const participantsHTML =
          details.participants.length > 0
            ? `<div class="participants-section">
              <h5>Participants:</h5>
              <ul class="participants-list">
                ${details.participants
                  .map(
                    (email) =>
                      `<li><span class="participant-email">${email}</span><button class="delete-btn" data-activity="${name}" data-email="${email}">❌</button></li>`
                  )
                  .join("")}
              </ul>
            </div>`
            : `<p><em>No participants yet</em></p>`;

        activityCard.innerHTML = `
          <h4>${name}</h4>
          <p>${details.description}</p>
          <p><strong>Schedule:</strong> ${details.schedule}</p>
          <p><strong>Availability:</strong> ${spotsLeft} spots left</p>
          <div class="participants-container">
            ${participantsHTML}
          </div>
          <button class="attendance-summary-btn" data-activity="${name}">📋 View Attendance</button>
        `;

        activitiesList.appendChild(activityCard);

        // Add option to select dropdowns
        [activitySelect, attendanceActivitySelect].forEach((sel) => {
          const option = document.createElement("option");
          option.value = name;
          option.textContent = name;
          sel.appendChild(option);
        });
      });

      // Add event listeners to delete buttons
      document.querySelectorAll(".delete-btn").forEach((button) => {
        button.addEventListener("click", handleUnregister);
      });

      // Add event listeners to attendance summary buttons
      document.querySelectorAll(".attendance-summary-btn").forEach((button) => {
        button.addEventListener("click", handleViewAttendanceSummary);
      });
    } catch (error) {
      activitiesList.innerHTML =
        "<p>Failed to load activities. Please try again later.</p>";
      console.error("Error fetching activities:", error);
    }
  }

  // Handle unregister functionality
  async function handleUnregister(event) {
    const button = event.target;
    const activity = button.getAttribute("data-activity");
    const email = button.getAttribute("data-email");

    try {
      const response = await fetch(
        `/activities/${encodeURIComponent(
          activity
        )}/unregister?email=${encodeURIComponent(email)}`,
        {
          method: "DELETE",
        }
      );

      const result = await response.json();

      if (response.ok) {
        messageDiv.textContent = result.message;
        messageDiv.className = "success";

        // Refresh activities list to show updated participants
        fetchActivities();
      } else {
        messageDiv.textContent = result.detail || "An error occurred";
        messageDiv.className = "error";
      }

      messageDiv.classList.remove("hidden");

      // Hide message after 5 seconds
      setTimeout(() => {
        messageDiv.classList.add("hidden");
      }, 5000);
    } catch (error) {
      messageDiv.textContent = "Failed to unregister. Please try again.";
      messageDiv.className = "error";
      messageDiv.classList.remove("hidden");
      console.error("Error unregistering:", error);
    }
  }

  // Handle form submission
  signupForm.addEventListener("submit", async (event) => {
    event.preventDefault();

    const email = document.getElementById("email").value;
    const activity = document.getElementById("activity").value;

    try {
      const response = await fetch(
        `/activities/${encodeURIComponent(
          activity
        )}/signup?email=${encodeURIComponent(email)}`,
        {
          method: "POST",
        }
      );

      const result = await response.json();

      if (response.ok) {
        messageDiv.textContent = result.message;
        messageDiv.className = "success";
        signupForm.reset();

        // Refresh activities list to show updated participants
        fetchActivities();
      } else {
        messageDiv.textContent = result.detail || "An error occurred";
        messageDiv.className = "error";
      }

      messageDiv.classList.remove("hidden");

      // Hide message after 5 seconds
      setTimeout(() => {
        messageDiv.classList.add("hidden");
      }, 5000);
    } catch (error) {
      messageDiv.textContent = "Failed to sign up. Please try again.";
      messageDiv.className = "error";
      messageDiv.classList.remove("hidden");
      console.error("Error signing up:", error);
    }
  });

  // ---------------------------------------------------------------------------
  // Attendance
  // ---------------------------------------------------------------------------

  // When attendance activity changes, load participants as checkboxes
  attendanceActivitySelect.addEventListener("change", async () => {
    const activity = attendanceActivitySelect.value;
    attendanceChecklist.innerHTML = "";
    submitAttendanceBtn.classList.add("hidden");
    attendanceReportContainer.classList.add("hidden");

    if (!activity) return;

    try {
      const response = await fetch("/activities");
      const activities = await response.json();
      const participants = activities[activity]?.participants || [];

      if (participants.length === 0) {
        attendanceChecklist.innerHTML = "<p><em>No participants registered for this activity.</em></p>";
        return;
      }

      attendanceChecklist.innerHTML = `
        <p><strong>Mark who attended:</strong></p>
        <ul class="attendance-checklist-list">
          ${participants
            .map(
              (email) => `
            <li>
              <label>
                <input type="checkbox" class="attendance-check" value="${email}" checked />
                ${email}
              </label>
            </li>`
            )
            .join("")}
        </ul>
      `;
      submitAttendanceBtn.classList.remove("hidden");
    } catch (error) {
      console.error("Error loading participants:", error);
    }
  });

  // Submit attendance
  submitAttendanceBtn.addEventListener("click", async () => {
    const activity = attendanceActivitySelect.value;
    const date = attendanceDateInput.value;

    if (!activity || !date) {
      showAttendanceMessage("Please select an activity and date.", "error");
      return;
    }

    const checked = Array.from(
      document.querySelectorAll(".attendance-check:checked")
    ).map((cb) => cb.value);

    try {
      const response = await fetch(
        `/activities/${encodeURIComponent(activity)}/attendance?date=${encodeURIComponent(date)}`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ present: checked }),
        }
      );

      const result = await response.json();

      if (response.ok) {
        showAttendanceMessage(
          `✅ Attendance saved for ${activity} on ${date}. Present: ${result.present.length}, Absent: ${result.absent.length}`,
          "success"
        );
      } else {
        showAttendanceMessage(result.detail || "An error occurred", "error");
      }
    } catch (error) {
      showAttendanceMessage("Failed to save attendance. Please try again.", "error");
      console.error("Error saving attendance:", error);
    }
  });

  // View attendance summary for an activity card button
  async function handleViewAttendanceSummary(event) {
    const activity = event.target.getAttribute("data-activity");

    try {
      const response = await fetch(
        `/activities/${encodeURIComponent(activity)}/attendance/summary`
      );
      const data = await response.json();

      if (!response.ok) {
        return;
      }

      attendanceReportContainer.classList.remove("hidden");

      if (data.total_sessions === 0) {
        attendanceReport.innerHTML = `<p><em>No attendance sessions recorded for <strong>${activity}</strong> yet.</em></p>`;
        return;
      }

      const rows = Object.entries(data.per_student)
        .sort(([, a], [, b]) => b.attendance_rate - a.attendance_rate)
        .map(([email, stats]) => `
          <tr>
            <td>${email}</td>
            <td>${stats.attended}</td>
            <td>${stats.missed}</td>
            <td>${(stats.attendance_rate * 100).toFixed(0)}%</td>
          </tr>
        `)
        .join("");

      attendanceReport.innerHTML = `
        <p><strong>${activity}</strong> — ${data.total_sessions} session(s) recorded</p>
        <table class="attendance-table">
          <thead>
            <tr><th>Student</th><th>Attended</th><th>Missed</th><th>Rate</th></tr>
          </thead>
          <tbody>${rows}</tbody>
        </table>
      `;

      // Scroll to report
      attendanceReportContainer.scrollIntoView({ behavior: "smooth" });
    } catch (error) {
      console.error("Error fetching attendance summary:", error);
    }
  }

  function showAttendanceMessage(text, type) {
    attendanceMessageDiv.textContent = text;
    attendanceMessageDiv.className = type;
    attendanceMessageDiv.classList.remove("hidden");
    setTimeout(() => attendanceMessageDiv.classList.add("hidden"), 6000);
  }

  // Initialize app
  fetchActivities();
});


  // Function to fetch activities from API
  async function fetchActivities() {
    try {
      const response = await fetch("/activities");
      const activities = await response.json();

      // Clear loading message
      activitiesList.innerHTML = "";

      // Populate activities list
      Object.entries(activities).forEach(([name, details]) => {
        const activityCard = document.createElement("div");
        activityCard.className = "activity-card";

        const spotsLeft =
          details.max_participants - details.participants.length;

        // Create participants HTML with delete icons instead of bullet points
        const participantsHTML =
          details.participants.length > 0
            ? `<div class="participants-section">
              <h5>Participants:</h5>
              <ul class="participants-list">
                ${details.participants
                  .map(
                    (email) =>
                      `<li><span class="participant-email">${email}</span><button class="delete-btn" data-activity="${name}" data-email="${email}">❌</button></li>`
                  )
                  .join("")}
              </ul>
            </div>`
            : `<p><em>No participants yet</em></p>`;

        activityCard.innerHTML = `
          <h4>${name}</h4>
          <p>${details.description}</p>
          <p><strong>Schedule:</strong> ${details.schedule}</p>
          <p><strong>Availability:</strong> ${spotsLeft} spots left</p>
          <div class="participants-container">
            ${participantsHTML}
          </div>
        `;

        activitiesList.appendChild(activityCard);

        // Add option to select dropdown
        const option = document.createElement("option");
        option.value = name;
        option.textContent = name;
        activitySelect.appendChild(option);
      });

      // Add event listeners to delete buttons
      document.querySelectorAll(".delete-btn").forEach((button) => {
        button.addEventListener("click", handleUnregister);
      });
    } catch (error) {
      activitiesList.innerHTML =
        "<p>Failed to load activities. Please try again later.</p>";
      console.error("Error fetching activities:", error);
    }
  }

  // Handle unregister functionality
  async function handleUnregister(event) {
    const button = event.target;
    const activity = button.getAttribute("data-activity");
    const email = button.getAttribute("data-email");

    try {
      const response = await fetch(
        `/activities/${encodeURIComponent(
          activity
        )}/unregister?email=${encodeURIComponent(email)}`,
        {
          method: "DELETE",
        }
      );

      const result = await response.json();

      if (response.ok) {
        messageDiv.textContent = result.message;
        messageDiv.className = "success";

        // Refresh activities list to show updated participants
        fetchActivities();
      } else {
        messageDiv.textContent = result.detail || "An error occurred";
        messageDiv.className = "error";
      }

      messageDiv.classList.remove("hidden");

      // Hide message after 5 seconds
      setTimeout(() => {
        messageDiv.classList.add("hidden");
      }, 5000);
    } catch (error) {
      messageDiv.textContent = "Failed to unregister. Please try again.";
      messageDiv.className = "error";
      messageDiv.classList.remove("hidden");
      console.error("Error unregistering:", error);
    }
  }

  // Handle form submission
  signupForm.addEventListener("submit", async (event) => {
    event.preventDefault();

    const email = document.getElementById("email").value;
    const activity = document.getElementById("activity").value;

    try {
      const response = await fetch(
        `/activities/${encodeURIComponent(
          activity
        )}/signup?email=${encodeURIComponent(email)}`,
        {
          method: "POST",
        }
      );

      const result = await response.json();

      if (response.ok) {
        messageDiv.textContent = result.message;
        messageDiv.className = "success";
        signupForm.reset();

        // Refresh activities list to show updated participants
        fetchActivities();
      } else {
        messageDiv.textContent = result.detail || "An error occurred";
        messageDiv.className = "error";
      }

      messageDiv.classList.remove("hidden");

      // Hide message after 5 seconds
      setTimeout(() => {
        messageDiv.classList.add("hidden");
      }, 5000);
    } catch (error) {
      messageDiv.textContent = "Failed to sign up. Please try again.";
      messageDiv.className = "error";
      messageDiv.classList.remove("hidden");
      console.error("Error signing up:", error);
    }
  });

  // Initialize app
  fetchActivities();
});
