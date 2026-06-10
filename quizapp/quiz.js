const optionButtons =
  document.querySelectorAll(".option-btn");

const scoreElement =
  document.getElementById("score");

let score = 0;

optionButtons.forEach(button => {

  button.addEventListener("click", () => {

    optionButtons.forEach(btn => {
      btn.classList.remove("active");
    });

    button.classList.add("active");

    if(button.textContent ===
      "Hyper Text Markup Language"){

      score = 1;
    }
    else{

      score = 0;
    }

    scoreElement.textContent = score;

  });

});

document.getElementById("nextBtn")
.addEventListener("click", () => {

  if (window.UIVERSE_DEBUG) alert("Next question feature can be extended.");

});

// quiz.js

const options = document.querySelectorAll(".option-btn");

options.forEach((btn) => {

  btn.addEventListener("click", () => {

    options.forEach((item) => {
      item.style.border = "1px solid rgba(255,255,255,0.08)";
      item.style.background = "rgba(255,255,255,0.06)";
    });

    btn.style.border = "2px solid #06b6d4";
    btn.style.background =
      "linear-gradient(135deg, rgba(139,92,246,0.35), rgba(6,182,212,0.35))";

  });

});

let time = 30;

const timer = document.getElementById("timer");

setInterval(() => {

  if(time > 0){
    time--;
    timer.innerText = time + "s";
  }

},1000);

const quizData = [
  {
    category: "Web Development",
    question: "What does HTML stand for?",
    options: [
      "Hyper Text Markup Language",
      "High Transfer Machine Language",
      "Hyper Transfer Markup Level",
      "Home Tool Markup Language"
    ],
    answer: 0
  },
  {
    category: "Web Development",
    question: "Which CSS property changes text color?",
    options: [
      "font-style",
      "text-color",
      "color",
      "background-color"
    ],
    answer: 2
  },
  {
    category: "JavaScript",
    question: "Which keyword declares a block-scoped variable?",
    options: [
      "var",
      "const",
      "let",
      "Both let and const"
    ],
    answer: 3
  },
  {
    category: "JavaScript",
    question: "Which method converts JSON text into an object?",
    options: [
      "JSON.parse()",
      "JSON.stringify()",
      "JSON.convert()",
      "JSON.object()"
    ],
    answer: 0
  },
  {
    category: "Programming",
    question: "Which data structure follows FIFO?",
    options: [
      "Stack",
      "Queue",
      "Tree",
      "Graph"
    ],
    answer: 1
  },
  {
    category: "Programming",
    question: "Which symbol is used for comments in JavaScript?",
    options: [
      "<!-- -->",
      "#",
      "//",
      "**"
    ],
    answer: 2
  },
  {
    category: "React",
    question: "What hook is used to manage state?",
    options: [
      "useState",
      "useFetch",
      "useMemo",
      "useRouter"
    ],
    answer: 0
  },
  {
    category: "React",
    question: "JSX stands for?",
    options: [
      "Java Syntax Extension",
      "JavaScript XML",
      "JSON XML",
      "Java Source XML"
    ],
    answer: 1
  },
  {
    category: "Database",
    question: "Which SQL command retrieves data?",
    options: [
      "INSERT",
      "UPDATE",
      "SELECT",
      "DELETE"
    ],
    answer: 2
  },
  {
    category: "Database",
    question: "What does SQL stand for?",
    options: [
      "Structured Query Language",
      "Simple Query Language",
      "Standard Question Language",
      "Sequential Query Logic"
    ],
    answer: 0
  },
  {
    category: "Cyber Security",
    question: "What does HTTPS provide?",
    options: [
      "Compression",
      "Encryption",
      "Caching",
      "Hosting"
    ],
    answer: 1
  },
  {
    category: "Computer Science",
    question: "Which algorithm is used for binary search?",
    options: [
      "Divide and Conquer",
      "Greedy",
      "Backtracking",
      "Dynamic Programming"
    ],
    answer: 0
  }
];