window.onload = function() {
    setTimeout(function() {
      var flashMessage = document.getElementById('flash-message');
      flashMessage.parentNode.removeChild(flashMessage);
    }, 3000);
  };