document.addEventListener("DOMContentLoaded", () => {
  const activitiesList = document.getElementById("activities-list");
  const activitySelect = document.getElementById("activity");
  const signupForm = document.getElementById("signup-form");
  const messageDiv = document.getElementById("message");

  // Function to fetch activities from API
  async function fetchActivities() {
    try {
      const response = await fetch("/activities");

      if (!response.ok) {
        throw new Error(`Failed to load activities: ${response.status}`);
      }

      const activities = await response.json();

      // Clear loading message
      activitiesList.innerHTML = "";
      activitySelect.innerHTML =
        '<option value="">-- Select an activity --</option>';

      const activitiesByCategory = Object.entries(activities).reduce(
        (categories, activity) => {
          const category = activity[1].category || "Other Activities";
          if (!categories[category]) {
            categories[category] = [];
          }
          categories[category].push(activity);
          return categories;
        },
        {}
      );

      Object.entries(activitiesByCategory).forEach(
        ([category, categoryActivities]) => {
          const categorySection = document.createElement("details");
          categorySection.className = "activity-category";
          categorySection.open = true;

          const categoryHeading = document.createElement("summary");
          categoryHeading.className = "category-heading";

          const categoryName = document.createElement("span");
          categoryName.textContent = category;

          const activityCount = document.createElement("span");
          activityCount.className = "category-count";
          activityCount.textContent = `${categoryActivities.length} ${
            categoryActivities.length === 1 ? "activity" : "activities"
          }`;

          categoryHeading.append(categoryName, activityCount);
          categorySection.appendChild(categoryHeading);

          const categoryContent = document.createElement("div");
          categoryContent.className = "category-content";

          const selectGroup = document.createElement("optgroup");
          selectGroup.label = category;

          categoryActivities.forEach(([name, details]) => {
            const activityCard = document.createElement("article");
            activityCard.className = "activity-card";

            const spotsLeft =
              details.max_participants - details.participants.length;

            activityCard.innerHTML = `
              <h5>${name}</h5>
              <p>${details.description}</p>
              <p><strong>Schedule:</strong> ${details.schedule}</p>
              <p><strong>Availability:</strong> ${spotsLeft} spots left</p>
            `;

            const participantsSection = document.createElement("div");
            participantsSection.className = "participants-section";

            const participantsHeading = document.createElement("h6");
            participantsHeading.textContent = `Registered students (${details.participants.length})`;
            participantsSection.appendChild(participantsHeading);

            if (details.participants.length > 0) {
              const participantsList = document.createElement("ul");
              participantsList.className = "participants-list";

              details.participants.forEach((email) => {
                const participant = document.createElement("li");
                participant.textContent = email;
                participantsList.appendChild(participant);
              });

              participantsSection.appendChild(participantsList);
            } else {
              const emptyMessage = document.createElement("p");
              emptyMessage.className = "participants-empty";
              emptyMessage.textContent = "No students are registered yet.";
              participantsSection.appendChild(emptyMessage);
            }

            activityCard.appendChild(participantsSection);
            categoryContent.appendChild(activityCard);

            const option = document.createElement("option");
            option.value = name;
            option.textContent = name;
            selectGroup.appendChild(option);
          });

          categorySection.appendChild(categoryContent);
          activitiesList.appendChild(categorySection);
          activitySelect.appendChild(selectGroup);
        }
      );
    } catch (error) {
      activitiesList.innerHTML = "<p>Failed to load activities. Please try again later.</p>";
      console.error("Error fetching activities:", error);
    }
  }

  // Handle form submission
  signupForm.addEventListener("submit", async (event) => {
    event.preventDefault();

    const emailUsername = document.getElementById("email").value.trim();
    const email = `${emailUsername}@mergington.edu`;
    const activity = document.getElementById("activity").value;

    try {
      const response = await fetch(
        `/activities/${encodeURIComponent(activity)}/signup?email=${encodeURIComponent(email)}`,
        {
          method: "POST",
        }
      );

      const result = await response.json();

      if (response.ok) {
        messageDiv.textContent = result.message;
        messageDiv.className = "success";
        signupForm.reset();
        await fetchActivities();
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
