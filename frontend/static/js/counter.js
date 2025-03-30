document.addEventListener('DOMContentLoaded', function () {
    const draftCountdown = document.getElementById('draftCountdown');
    const nextDraftCountdown = document.getElementById('nextDraftCountdown');
  
    function updateCountdown(element, startTime, endTime, isComplete = null) {
      const now = new Date();
      const start = new Date(startTime);
      const end = new Date(endTime);
  
      let targetTime;
      let label;
  
      if (isComplete !== null) {
        // Player Portal Logic
        if (isComplete) {
          targetTime = start;
          label = "Next Draft Opens In:";
        } else {
          targetTime = end;
          label = "Draft Ends In:";
        }
      } else {
        // Home Page Logic
        targetTime = start;
        label = "Next Draft Opens In:";
      }
  
      const distance = targetTime - now;
      if (distance <= 0) {
        element.innerHTML = "Draft Window Open!";
        return;
      }
  
      const days = Math.floor(distance / (1000 * 60 * 60 * 24));
      const hours = Math.floor((distance % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
      const minutes = Math.floor((distance % (1000 * 60 * 60)) / (1000 * 60));
      const seconds = Math.floor((distance % (1000 * 60)) / 1000);
  
      element.innerHTML = `${days}:${hours}:${minutes}:${seconds}`;
    }
  
    if (draftCountdown) {
      const startTime = draftCountdown.getAttribute('data-start');
      const endTime = draftCountdown.getAttribute('data-end');
      const isComplete = draftCountdown.getAttribute('data-complete') === 'true';
  
      updateCountdown(draftCountdown, startTime, endTime, isComplete);
      setInterval(() => updateCountdown(draftCountdown, startTime, endTime, isComplete), 1000);
    }
  
    if (nextDraftCountdown) {
      const startTime = nextDraftCountdown.getAttribute('data-start');
      const endTime = nextDraftCountdown.getAttribute('data-end');
  
      updateCountdown(nextDraftCountdown, startTime, endTime);
      setInterval(() => updateCountdown(nextDraftCountdown, startTime, endTime), 1000);
    }
  });
  