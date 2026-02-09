/**
 * Global Theme System for CyberTec8 CTF Platform
 * Manages light/dark theme across all pages with localStorage persistence
 */

(function() {
  'use strict';
  
  const THEME_KEY = 'cybertec8-theme';
  const DEFAULT_THEME = 'dark';
  
  // Theme Manager Class
  class ThemeManager {
    constructor() {
      this.currentTheme = this.loadTheme();
      this.init();
    }
    
    // Load theme from localStorage or use default
    loadTheme() {
      return localStorage.getItem(THEME_KEY) || DEFAULT_THEME;
    }
    
    // Save theme to localStorage
    saveTheme(theme) {
      localStorage.setItem(THEME_KEY, theme);
    }
    
    // Apply theme to document
    applyTheme(theme) {
      const root = document.documentElement;
      
      // Apply theme to root element immediately (prevents FOUC)
      root.setAttribute('data-theme', theme);
      
      this.currentTheme = theme;
      
      // Handle body classes and transitions if body is available
      if (document.body) {
        this._applyToBody(theme);
      } else {
        // If body not ready, wait for DOMContentLoaded
        document.addEventListener('DOMContentLoaded', () => {
          this._applyToBody(theme);
        });
      }
      
      // Update buttons if DOM is ready, otherwise listeners will handle it
      if (document.readyState !== 'loading') {
        this.updateToggleButton();
      }
    }
    
    // Internal method to apply theme classes to body
    _applyToBody(theme) {
      const body = document.body;
      if (!body) return;
      
      // Remove transition class temporarily
      body.classList.add('no-transition');
      
      // Also add class for compatibility
      if (theme === 'light') {
        body.classList.add('light-theme');
        body.classList.remove('dark-theme');
      } else {
        body.classList.add('dark-theme');
        body.classList.remove('light-theme');
      }
      
      // Re-enable transitions after a frame
      requestAnimationFrame(() => {
        body.classList.remove('no-transition');
      });
      
      this.updateToggleButton();
    }
    
    // Toggle between light and dark
    toggle() {
      const newTheme = this.currentTheme === 'dark' ? 'light' : 'dark';
      this.applyTheme(newTheme);
      this.saveTheme(newTheme);
      
      // Dispatch custom event for other scripts to listen
      window.dispatchEvent(new CustomEvent('themeChange', { detail: { theme: newTheme } }));
    }
    
    // Update toggle button icons
    updateToggleButton() {
      const moonIcons = document.querySelectorAll('.theme-icon-moon');
      const sunIcons = document.querySelectorAll('.theme-icon-sun');
      
      if (this.currentTheme === 'light') {
        moonIcons.forEach(icon => {
          icon.style.opacity = '0';
          icon.style.transform = 'rotate(-180deg) scale(0)';
        });
        sunIcons.forEach(icon => {
          icon.style.opacity = '1';
          icon.style.transform = 'rotate(0deg) scale(1)';
        });
      } else {
        moonIcons.forEach(icon => {
          icon.style.opacity = '1';
          icon.style.transform = 'rotate(0deg) scale(1)';
        });
        sunIcons.forEach(icon => {
          icon.style.opacity = '0';
          icon.style.transform = 'rotate(180deg) scale(0)';
        });
      }
    }
    
    // Initialize theme system
    init() {
      // Apply theme immediately (before page render)
      this.applyTheme(this.currentTheme);
      
      // Wait for DOM to be ready
      if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => this.setupListeners());
      } else {
        this.setupListeners();
      }
    }
    
    // Setup event listeners for toggle buttons
    setupListeners() {
      const toggleButtons = document.querySelectorAll('.theme-toggle-btn, #themeToggle, [data-theme-toggle]');
      
      toggleButtons.forEach(button => {
        button.addEventListener('click', (e) => {
          e.preventDefault();
          this.toggle();
        });
      });
      
      // Update button states
      this.updateToggleButton();
    }
    
    // Get current theme
    getTheme() {
      return this.currentTheme;
    }
  }
  
  // Create global theme manager instance
  window.ThemeManager = new ThemeManager();
  
  // Expose utility functions
  window.getTheme = () => window.ThemeManager.getTheme();
  window.setTheme = (theme) => {
    if (theme === 'light' || theme === 'dark') {
      window.ThemeManager.applyTheme(theme);
      window.ThemeManager.saveTheme(theme);
    }
  };
  window.toggleTheme = () => window.ThemeManager.toggle();
  
})();
