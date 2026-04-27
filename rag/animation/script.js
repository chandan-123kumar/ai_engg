const steps = [
  {
    title: "PDF text extraction",
    text:
      "A PDF is not searched directly. First, the program extracts readable text from each page.",
  },
  {
    title: "Chunking",
    text:
      "Large pages are divided into smaller overlapping chunks so each piece is short enough to embed and retrieve accurately.",
  },
  {
    title: "Embeddings",
    text:
      "The embedding model turns each text chunk into a vector: a list of numbers that represents meaning.",
  },
  {
    title: "ChromaDB storage",
    text:
      "ChromaDB stores the vectors with metadata such as source file, page number, and chunk number.",
  },
  {
    title: "Similarity search",
    text:
      "A question is embedded too. ChromaDB compares vectors and returns the chunks closest in meaning.",
  },
];

const stages = [...document.querySelectorAll(".stage")];
const movingToken = document.querySelector("#movingToken");
const stepTitle = document.querySelector("#stepTitle");
const stepText = document.querySelector("#stepText");
const playPauseBtn = document.querySelector("#playPauseBtn");
const restartBtn = document.querySelector("#restartBtn");

let currentStep = 0;
let isPlaying = true;
let timerId = null;

function tokenPositionForStep(stepIndex) {
  if (stages.length === 1) return "50%";
  const start = 8;
  const end = 92;
  const progress = stepIndex / (stages.length - 1);
  return `${start + (end - start) * progress}%`;
}

function showStep(stepIndex) {
  currentStep = stepIndex;

  stages.forEach((stage, index) => {
    stage.classList.toggle("active", index === currentStep);
  });

  const step = steps[currentStep];
  stepTitle.textContent = step.title;
  stepText.textContent = step.text;
  movingToken.style.left = tokenPositionForStep(currentStep);
}

function scheduleNextStep() {
  window.clearTimeout(timerId);

  if (!isPlaying) return;

  timerId = window.setTimeout(() => {
    showStep((currentStep + 1) % steps.length);
    scheduleNextStep();
  }, 2500);
}

function restartAnimation() {
  isPlaying = true;
  playPauseBtn.textContent = "Pause";
  showStep(0);
  scheduleNextStep();
}

playPauseBtn.addEventListener("click", () => {
  isPlaying = !isPlaying;
  playPauseBtn.textContent = isPlaying ? "Pause" : "Play";
  scheduleNextStep();
});

restartBtn.addEventListener("click", restartAnimation);

stages.forEach((stage, index) => {
  stage.addEventListener("click", () => {
    showStep(index);
    scheduleNextStep();
  });
});

showStep(0);
scheduleNextStep();
