document.addEventListener("DOMContentLoaded", () => {
  document
    .querySelectorAll("table.config-table code.literal")
    .forEach((code) => {
      code.innerHTML = code.innerHTML.replace(/_/g, "_<wbr>");
    });
});
