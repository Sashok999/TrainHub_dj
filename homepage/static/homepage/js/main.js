"use strict";

// Помощь при поиске: повторная отправка формы с пустыми полями не выполняется.
document.querySelectorAll(".search-form").forEach((form) => {
  const button = form.querySelector('button[type="submit"]');
  const update = () => {
    button.disabled = !Array.from(form.querySelectorAll("[required]"))
      .every((field) => field.value && field.validity.valid);
  };
  form.addEventListener("input", update);
  form.addEventListener("change", update);
  update();
});
