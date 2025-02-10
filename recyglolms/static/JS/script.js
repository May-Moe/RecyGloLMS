document.addEventListener('DOMContentLoaded', function () {
    const toggleButton = document.getElementById('toggle-button');
    const sidebar = document.querySelector('.sidebar'); // Adjust the selector to match your sidebar

    toggleButton.addEventListener('click', function () {
        sidebar.classList.toggle('open'); // Toggle the 'active' class on the sidebar
    });
});

document.addEventListener("DOMContentLoaded", () => {
    const notificationButton = document.getElementById("notification-button");
    const notificationDropdown = document.getElementById("notification-dropdown");

    notificationButton.addEventListener("click", () => {
        notificationDropdown.classList.toggle("active"); // Toggle visibility
    });

    // Optional: Close the dropdown when clicking outside
    document.addEventListener("click", (event) => {
        if (!notificationButton.contains(event.target) && 
            !notificationDropdown.contains(event.target)) {
            notificationDropdown.classList.remove("active");
        }
    });
});
// JavaScript for Add Button Dropdown
document.addEventListener("DOMContentLoaded", function () {
    const addButton = document.getElementById("addUserButton");
    const dropdownMenu = document.getElementById("addCourseDropdown");

    addButton.addEventListener("click", function (e) {
        e.stopPropagation(); // Prevent click event from propagating
        dropdownMenu.classList.toggle("active");
    });

    // Close dropdown when clicking outside
    document.addEventListener("click", function () {
        dropdownMenu.classList.remove("active");
    });
});

// for user profile dropdown

// Function to toggle the dropdown menu
function toggleDropdown() {
  const dropdown = document.getElementById("profile-dropdown");
  dropdown.classList.toggle("hidden");
}

// Close the dropdown if the user clicks outside of it
window.addEventListener("click", function (event) {
  const dropdown = document.getElementById("profile-dropdown");
  const profilePic = document.getElementById("profile-pic-right");
  if (!profilePic.contains(event.target) && !dropdown.contains(event.target)) {
      dropdown.classList.add("hidden");
  }
});


// document.addEventListener('DOMContentLoaded', () => {
//     const calendarMonthYear = document.getElementById('calendar-month-year');
//     const calendarDates = document.getElementById('calendar-dates');
//     const prevMonthButton = document.getElementById('prev-month');
//     const nextMonthButton = document.getElementById('next-month');

//     let currentDate = new Date();

//     function renderCalendar() {
//         const year = currentDate.getFullYear();
//         const month = currentDate.getMonth();

//         // Update header
//         const monthNames = [
//             'January', 'February', 'March', 'April', 'May', 'June', 
//             'July', 'August', 'September', 'October', 'November', 'December'
//         ];
//         calendarMonthYear.textContent = `${monthNames[month]} ${year}`;

//         // Clear previous dates
//         calendarDates.innerHTML = '';

//         // First day of the month (0 = Sunday, 1 = Monday, ..., 6 = Saturday)
//         const firstDay = new Date(year, month, 1).getDay();

//         // Total days in the current month
//         const daysInMonth = new Date(year, month + 1, 0).getDate();

//         // Previous month's last few days for the leading empty spaces
//         const prevMonthDays = new Date(year, month, 0).getDate();

//         // Create the full calendar grid (6 rows, 7 columns = 42 slots)
//         const totalSlots = 42;
//         let dayCount = 1;
//         let nextMonthDayCount = 1;

//         for (let i = 0; i < totalSlots; i++) {
//             const dateElement = document.createElement('div');
//             dateElement.classList.add('calendar-date');

//             if (i < firstDay) {
//                 // Fill leading days from the previous month
//                 dateElement.textContent = prevMonthDays - firstDay + i + 1;
//                 dateElement.classList.add('inactive');
//             } else if (dayCount <= daysInMonth) {
//                 // Fill current month's days
//                 dateElement.textContent = dayCount;

//                 // Highlight today's date
//                 if (
//                     dayCount === new Date().getDate() &&
//                     month === new Date().getMonth() &&
//                     year === new Date().getFullYear()
//                 ) {
//                     dateElement.classList.add('today');
//                 }

//                 dayCount++;
//             } else {
//                 // Fill trailing days for the next month
//                 dateElement.textContent = nextMonthDayCount++;
//                 dateElement.classList.add('inactive');
//             }

//             calendarDates.appendChild(dateElement);
//         }
//     }

//     // Handle navigation
//     prevMonthButton.addEventListener('click', () => {
//         currentDate.setMonth(currentDate.getMonth() - 1);
//         renderCalendar();
//     });

//     nextMonthButton.addEventListener('click', () => {
//         currentDate.setMonth(currentDate.getMonth() + 1);
//         renderCalendar();
//     });

//     renderCalendar();
// });


let display = document.querySelector(".display");
let days = document.querySelector(".days");
let previous = document.querySelector(".left");
let next = document.querySelector(".right");
let selected = document.querySelector(".selected");

let date = new Date();

let year = date.getFullYear();
let month = date.getMonth();

function displayCalendar() {
  const firstDay = new Date(year, month, 1);

  const lastDay = new Date(year, month + 1, 0);

  const firstDayIndex = firstDay.getDay(); //4

  const numberOfDays = lastDay.getDate(); //31

  let formattedDate = date.toLocaleString("en-US", {
    month: "long",
    year: "numeric"
  });

  display.innerHTML = `${formattedDate}`;

  for (let x = 1; x <= firstDayIndex; x++) {
    const div = document.createElement("div");
    div.innerHTML += "";

    days.appendChild(div);
  }

  for (let i = 1; i <= numberOfDays; i++) {
    let div = document.createElement("div");
    let currentDate = new Date(year, month, i);

    div.dataset.date = currentDate.toDateString();

    div.innerHTML += i;
    days.appendChild(div);
    if (
      currentDate.getFullYear() === new Date().getFullYear() &&
      currentDate.getMonth() === new Date().getMonth() &&
      currentDate.getDate() === new Date().getDate()
    ) {
      div.classList.add("current-date");
    }
  }
}

// Call the function to display the calendar
displayCalendar();

previous.addEventListener("click", () => {
  days.innerHTML = "";
  selected.innerHTML = "";

  if (month < 0) {
    month = 11;
    year = year - 1;
  }

  month = month - 1;

  date.setMonth(month);

  displayCalendar();
  displaySelected();
});

next.addEventListener("click", () => {
  days.innerHTML = "";
  selected.innerHTML = "";

  if (month > 11) {
    month = 0;
    year = year + 1;
  }

  month = month + 1;
  date.setMonth(month);

  displayCalendar();
  displaySelected();
});

function displaySelected() {
  const dayElements = document.querySelectorAll(".days div");
  dayElements.forEach((day) => {
    day.addEventListener("click", (e) => {
      const selectedDate = e.target.dataset.date;
      selected.innerHTML = `Selected Date : ${selectedDate}`;
    });
  });
}
displaySelected();


document.addEventListener("DOMContentLoaded", () => {
    const questionItems = document.getElementById("questionItems");
    const addQuestionButton = document.getElementById("addQuestion");
    const questionForm = document.getElementById("questionForm");
    const addChoiceButton = document.getElementById("addChoice");
    const choicesContainer = document.querySelector(".choices-container");
    const saveQuizButton = document.getElementById("saveQuiz");

    // Add new question
    addQuestionButton.addEventListener("click", () => {
        const newQuestion = prompt("Enter the new question:");
        if (newQuestion) {
            const li = document.createElement("li");
            li.className = "question-item";
            li.innerHTML = `
                ${newQuestion}
                <button class="delete-question" onclick="this.parentElement.remove()"><i class="fas fa-trash"></i></button>
            `;
            questionItems.appendChild(li);
        }
    });

    // Add new choice
    addChoiceButton.addEventListener("click", (e) => {
        e.preventDefault();

        const choiceDiv = document.createElement("div");
        choiceDiv.className = "choice";

        const radioInput = document.createElement("input");
        radioInput.type = "radio";
        radioInput.name = "correctAnswer";

        const textInput = document.createElement("input");
        textInput.type = "text";
        textInput.className = "choiceText";
        textInput.placeholder = `Choice ${choicesContainer.children.length + 1}`;

        const deleteButton = document.createElement("button");
        deleteButton.className = "delete-choice";
        deleteButton.innerHTML = '<i class="fas fa-trash"></i>';
        deleteButton.addEventListener("click", () => choiceDiv.remove());

        choiceDiv.appendChild(radioInput);
        choiceDiv.appendChild(textInput);
        choiceDiv.appendChild(deleteButton);
        choicesContainer.appendChild(choiceDiv);
    });

    // Save quiz
    saveQuizButton.addEventListener("click", (e) => {
        e.preventDefault();

        const quizData = {
            title: document.getElementById("quizTitle").value,
            description: document.getElementById("quizDescription").value,
            questions: [],
        };

        const questionElements = document.querySelectorAll(".question-item");
        questionElements.forEach((item, index) => {
            const questionText = item.textContent.trim();
            const choices = [];
            const choiceInputs = document.querySelectorAll(".choiceText");

            choiceInputs.forEach((input, i) => {
                choices.push({
                    text: input.value,
                    is_correct: document.querySelectorAll("input[name='correctAnswer']")[i].checked,
                });
            });

            quizData.questions.push({
                question: questionText,
                choices: choices,
            });
        });

        fetch(`/quiz/manage/${quiz_id}`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify(quizData),
        })
        .then(response => response.json())
        .then(data => alert(data.message))
        .catch(error => console.error("Error:", error));
    });
});