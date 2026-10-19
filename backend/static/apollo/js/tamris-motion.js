/* TAMRIS motion and polish.
 * Decoration only: if this script fails or is blocked, every page still works.
 */
(function () {
    'use strict';

    var reduceMotion = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;

    // ── Loader: leave quickly once the page is ready ───────────────────────────
    function hideLoader() {
        var loader = document.getElementById('loading-wrapper');
        if (!loader) return;
        if (window.jQuery) window.jQuery(loader).stop(true, true);  // cancel the theme's 3-second fade
        loader.style.display = '';
        loader.classList.add('tamris-hide');
        setTimeout(function () { loader.style.display = 'none'; }, 480);
    }

    // ── Progress bar while the next page loads ─────────────────────────────────
    var bar = document.createElement('div');
    bar.id = 'tamris-progress';
    var timer = null;

    function startProgress() {
        if (reduceMotion) return;
        clearInterval(timer);
        var width = 8;
        bar.style.width = width + '%';
        bar.classList.add('is-active');
        timer = setInterval(function () {
            width += (90 - width) * 0.08;  // creeps towards 90% until the new page arrives
            bar.style.width = width + '%';
        }, 200);
    }

    function stopProgress() {
        clearInterval(timer);
        if (!bar.classList.contains('is-active')) return;
        bar.style.width = '100%';
        setTimeout(function () {
            bar.classList.remove('is-active');
            bar.style.width = '0';
        }, 300);
    }

    function isPageLink(a, event) {
        if (!a || event.defaultPrevented || event.button !== 0) return false;
        if (event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return false;
        var href = a.getAttribute('href');
        if (!href || href.charAt(0) === '#' || href.indexOf('javascript:') === 0) return false;
        if (a.target && a.target !== '_self') return false;
        if (a.hasAttribute('download') || a.hasAttribute('data-bs-toggle')) return false;
        if (a.host && a.host !== window.location.host) return false;
        return true;
    }

    document.addEventListener('click', function (event) {
        var a = event.target.closest ? event.target.closest('a') : null;
        if (isPageLink(a, event)) startProgress();
    });
    document.addEventListener('submit', function (event) {
        var form = event.target;
        if (!event.defaultPrevented && (!form.target || form.target === '_self')) startProgress();
    });
    // Back/forward cache and pages that open a file in place: never leave the bar running
    window.addEventListener('pageshow', stopProgress);
    window.addEventListener('pagehide', function () { clearInterval(timer); });

    // ── Cards rise in one after another ────────────────────────────────────────
    function revealCards() {
        var cards = document.querySelectorAll('.app-body .card, .app-body > .row > [class*="col"] > .alert');
        if (!cards.length || reduceMotion || !('IntersectionObserver' in window)) return;
        var observer = new IntersectionObserver(function (entries) {
            entries.forEach(function (entry) {
                if (entry.isIntersecting) {
                    entry.target.classList.add('is-visible');
                    observer.unobserve(entry.target);
                }
            });
        }, { threshold: 0.05 });
        var index = 0;
        Array.prototype.forEach.call(cards, function (card) {
            if (card.parentElement && card.parentElement.closest('.card')) return;  // only outer cards
            card.style.setProperty('--tamris-delay', Math.min(index, 8) * 0.06 + 's');
            card.classList.add('tamris-reveal');
            observer.observe(card);
            index += 1;
        });
    }

    // ── Dashboard numbers count up ─────────────────────────────────────────────
    function countUp() {
        if (reduceMotion) return;
        var selectors = '.app-body h2.m-0, .app-body .display-6, .app-body .fs-4.fw-bold, [data-countup]';
        Array.prototype.forEach.call(document.querySelectorAll(selectors), function (el) {
            if (el.children.length) return;
            var text = el.textContent.trim();
            if (!/^\d{1,7}$/.test(text)) return;
            var target = parseInt(text, 10);
            if (target === 0) return;
            var start = null;
            var duration = Math.min(1200, 500 + target * 25);
            el.textContent = '0';
            function step(ts) {
                if (start === null) start = ts;
                var p = Math.min(1, (ts - start) / duration);
                var eased = 1 - Math.pow(1 - p, 3);
                el.textContent = Math.round(target * eased).toLocaleString();
                if (p < 1) window.requestAnimationFrame(step);
                else el.textContent = text;
            }
            window.requestAnimationFrame(step);
        });
    }

    // ── Greeting by time of day on the welcome card ────────────────────────────
    function greet() {
        var heading = document.querySelector('.bg-3 h6');
        if (!heading || !/welcome back/i.test(heading.textContent)) return;
        var hour = new Date().getHours();
        var greeting = hour < 12 ? 'Good morning,' : hour < 17 ? 'Good afternoon,' : 'Good evening,';
        heading.textContent = greeting;
    }

    document.addEventListener('DOMContentLoaded', function () {
        document.body.appendChild(bar);
        greet();
        revealCards();
        countUp();
        setTimeout(hideLoader, 150);
    });
})();
