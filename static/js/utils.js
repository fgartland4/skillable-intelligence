/**
 * utils.js — Shared utility functions for the Designer frontend.
 * Loaded before phase controllers; provides escHtml, formatDate, and $ helpers.
 */

const Utils = (() => {

    /**
     * Escape HTML special characters to prevent XSS.
     * Uses a real DOM element for correct encoding.
     */
    function escHtml(str) {
        if (!str) return '';
        const div = document.createElement('div');
        div.textContent = str;
        return div.innerHTML;
    }

    /**
     * Format an ISO date string to a short locale-friendly display.
     */
    function formatDate(isoStr) {
        if (!isoStr) return '';
        try {
            const d = new Date(isoStr);
            return d.toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' });
        } catch {
            return '';
        }
    }

    /**
     * Short querySelector helper.
     */
    function $(sel, ctx) {
        return (ctx || document).querySelector(sel);
    }

    /**
     * Short querySelectorAll helper (returns array).
     */
    function $$(sel, ctx) {
        return [...(ctx || document).querySelectorAll(sel)];
    }

    return { escHtml, formatDate, $, $$ };

})();
