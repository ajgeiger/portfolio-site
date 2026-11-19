// Scroll to a #section link once Dash has drawn the page that holds it.
(function () {
  function scrollToHash() {
    if (!window.location.hash) {
      return true;
    }
    var target = document.getElementById(window.location.hash.slice(1));
    if (target) {
      target.scrollIntoView({ behavior: "smooth", block: "start" });
      return true;
    }
    return false;
  }

  function scrollWhenReady() {
    var attempts = 0;
    var timer = window.setInterval(function () {
      attempts += 1;
      if (scrollToHash() || attempts > 40) {
        window.clearInterval(timer);
      }
    }, 100);
  }

  // Anchor links from another page load the home page first, then scroll.
  document.addEventListener("click", function (event) {
    var link = event.target.closest("a[href*='#']");
    if (!link || link.target === "_blank") {
      return;
    }
    var url = new URL(link.href, window.location.href);
    if (url.origin !== window.location.origin || !url.hash) {
      return;
    }
    event.preventDefault();
    if (url.pathname !== window.location.pathname) {
      window.history.pushState({}, "", url.pathname + url.hash);
      window.dispatchEvent(new CustomEvent("_dashprivate_pushstate"));
    } else {
      window.history.replaceState({}, "", url.hash);
    }
    scrollWhenReady();
  });

  window.addEventListener("load", scrollWhenReady);
})();
