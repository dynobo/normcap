/*!
 * Minimal theme switcher
 *
 * Pico.css - https://picocss.com
 * Copyright 2020 - Licensed under MIT
 */

const themeSwitcher = {

  // Config
  buttonsTarget: 'a[data-theme-switcher]',
  buttonAttribute: 'data-theme-switcher',
  rootAttribute: 'data-theme',

  // Init
  init() {
    document.querySelectorAll(this.buttonsTarget).forEach(function(button) {
      button.addEventListener('click', function(event) {
      event.preventDefault();
      document.querySelector('html').setAttribute(
        this.rootAttribute,
        event.target.getAttribute(this.buttonAttribute));
      }.bind(this), false);
    }.bind(this));
  }
}

// Init
themeSwitcher.init();


const detailsToggler = {
  onMutation(mutationList, observer) {
    mutationList.forEach(function(mutation) {
      if (mutation.type === 'attributes' && mutation.attributeName === 'open') {
        let id = mutation.target.getAttribute("id");
        if (id) {
          history.pushState({},"", window.location.href.split('#')[0] + "#" + id);
        }
      }
    })
  },

  init() {
    // Open details if hash, adjust scroll a bit
    const hash = document.location.hash
    if (hash.startsWith("#faqs-") || hash.startsWith("#python-package-")) {
      const id = hash.slice(1);
      const detail = document.getElementById(id);
      detail.setAttribute("open", "");
      window.setTimeout(function(){
        window.scrollTo(window.scrollX, window.scrollY - 100);
      }, 10);
    }

    // Adjust hash on details open
    const observer = new MutationObserver(this.onMutation);
    document.querySelectorAll("details").forEach(function(detail) {
      observer.observe(detail, {attributes: true});
    });
  }
}

detailsToggler.init();
