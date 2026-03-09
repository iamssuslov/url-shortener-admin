const STORAGE_KEY = "url-shortener-theme";

function applyTheme(theme) {
  document.documentElement.setAttribute("data-theme", theme);
}

function getPreferredTheme() {
  const saved = localStorage.getItem(STORAGE_KEY);
  if (saved === "light" || saved === "dark") {
    return saved;
  }
  return "dark";
}

document.addEventListener("DOMContentLoaded", () => {
  const initialTheme = getPreferredTheme();
  applyTheme(initialTheme);

  const toggle = document.querySelector("[data-theme-toggle]");
  if (toggle) {
    toggle.addEventListener("click", () => {
      const current = document.documentElement.getAttribute("data-theme") || "dark";
      const next = current === "dark" ? "light" : "dark";
      localStorage.setItem(STORAGE_KEY, next);
      applyTheme(next);
    });
  }
});