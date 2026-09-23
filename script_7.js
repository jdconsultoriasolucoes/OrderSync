function updateCharCounter(textareaId, counterId) {
      const textarea = document.getElementById(textareaId);
      const counter = document.getElementById(counterId);
      if (textarea && counter) {
        counter.textContent = `${textarea.value.length} / 1000`;
      }
    }