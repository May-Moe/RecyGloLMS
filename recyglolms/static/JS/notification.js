document.addEventListener("DOMContentLoaded", function () {
    const notificationButton = document.getElementById("notification-button");
    const notificationDropdown = document.getElementById("notification-dropdown");
    const notificationCount = document.getElementById("notification-count");
    const notificationList = document.getElementById("notification-list");

    // Fetch notifications from the backend
    function fetchNotifications() {
        fetch("/notifications")
            .then(response => response.json())
            .then(data => {
                notificationList.innerHTML = "";
                if (data.notifications.length > 0) {
                    data.notifications.forEach(notification => {
                        let li = document.createElement("li");
                        li.textContent = notification.message;
                        notificationList.appendChild(li);
                    });
                    notificationCount.textContent = data.count;
                    notificationCount.style.display = "inline";
                } else {
                    notificationList.innerHTML = "<li>No new notifications.</li>";
                    notificationCount.style.display = "none";
                }
            })
            .catch(error => console.error("Error fetching notifications:", error));
    }

    // Show/Hide Notification Dropdown & Mark Notifications as Read
    notificationButton.addEventListener("click", function () {
        notificationDropdown.classList.toggle("hidden"); // Toggle the dropdown visibility
        fetchNotifications(); // Fetch notifications when opening the dropdown

        // Mark notifications as read only when the dropdown is opened
        fetch("/notifications/mark-read", { method: "POST" })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    notificationCount.style.display = "none"; // Hide the notification count once read
                }
            })
            .catch(error => console.error("Error marking notifications as read:", error));
    });

    // Fetch notifications on page load to ensure data is up-to-date
    fetchNotifications();
});