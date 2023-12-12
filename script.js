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
  openDetailFromHash() {
    let hash = window.location.hash;
    if (hash.startsWith("#faqs-") || hash.startsWith("#python-package-")) {
      const detail = document.getElementById(hash.slice(1));
      detail.setAttribute("open", "");
    }
  },

  onDetailClick(event) {
    let detail = event.target.parentNode;
    let isDetail = detail.nodeName == "DETAILS";
    let isOpened = !!(detail.getAttribute("open") != "");
    if (isDetail && isOpened) {
      history.replaceState(undefined, undefined, "#"+detail.id)
    }
  },

  addDetailStateChangeListeners(){
    self = this;
    document.querySelectorAll("details").forEach(function(detail) {
      detail.addEventListener("click", self.onDetailClick)
    });
  },

  addHashChangeListener(){
    self = this;
    window.addEventListener('hashchange', function () {
      self.openDetailFromHash()
    });
  },

  init() {
    this.openDetailFromHash();
    this.addHashChangeListener();
    this.addDetailStateChangeListeners();
  }
}

detailsToggler.init();
