/**
 * EventTrust (TrustChain v2.5) — Tactical Motion Engine
 * Reusable 3D Tilt, Counter Tweens, Viewport Stagger, and Visibility Optimization
 */

(function() {
    'use strict';

    // 1. Global Visibility State to prevent unnecessary background rendering
    window.__isTabActive = !document.hidden;
    document.addEventListener('visibilitychange', function() {
        window.__isTabActive = !document.hidden;
    }, { passive: true });

    // Check prefers-reduced-motion
    var prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

    // 2. 3D Card Perspective Tilt with Dynamic Specular Glare
    function initCardTilt3D() {
        if (prefersReducedMotion) return;

        var cards = document.querySelectorAll('.eoc-kpi-card, .eoc-tilt-card, .analytics-kpi-card, .details-row');
        if (!cards || cards.length === 0) return;

        cards.forEach(function(card) {
            if (card.__tiltInitialized) return;
            card.__tiltInitialized = true;

            var bounds = null;

            function onMouseEnter() {
                bounds = card.getBoundingClientRect();
            }

            function onMouseMove(e) {
                if (!bounds) bounds = card.getBoundingClientRect();
                var mouseX = e.clientX - bounds.left;
                var mouseY = e.clientY - bounds.top;

                var xPct = mouseX / bounds.width;
                var yPct = mouseY / bounds.height;

                // Restrained, premium tilt angle (+/- 4 to 5 degrees)
                var rotY = (xPct - 0.5) * 8.0;
                var rotX = (0.5 - yPct) * 8.0;

                card.style.transform = 'perspective(900px) rotateX(' + rotX.toFixed(2) + 'deg) rotateY(' + rotY.toFixed(2) + 'deg) scale3d(1.018, 1.018, 1.018)';
                card.style.setProperty('--mouse-x', (xPct * 100).toFixed(1) + '%');
                card.style.setProperty('--mouse-y', (yPct * 100).toFixed(1) + '%');
            }

            function onMouseLeave() {
                bounds = null;
                card.style.transform = 'perspective(900px) rotateX(0deg) rotateY(0deg) scale3d(1, 1, 1)';
            }

            card.addEventListener('mouseenter', onMouseEnter, { passive: true });
            card.addEventListener('mousemove', onMouseMove, { passive: true });
            card.addEventListener('mouseleave', onMouseLeave, { passive: true });
        });
    }

    // 3. Smooth Numerical Counters
    function initCounterAnimations() {
        if (prefersReducedMotion) return;

        var counterElements = document.querySelectorAll('.eoc-counter, [data-counter-target]');
        if (!counterElements || counterElements.length === 0) return;

        var observer = new IntersectionObserver(function(entries, obs) {
            entries.forEach(function(entry) {
                if (entry.isIntersecting) {
                    var el = entry.target;
                    obs.unobserve(el);

                    var rawText = el.getAttribute('data-counter-target') || el.innerText;
                    var match = rawText.match(/([\d\.]+)/);
                    if (!match) return;

                    var targetVal = parseFloat(match[1]);
                    var prefix = rawText.substring(0, match.index);
                    var suffix = rawText.substring(match.index + match[0].length);
                    var isFloat = rawText.includes('.');
                    var decimals = isFloat ? (match[1].split('.')[1] || '').length : 0;

                    var startTime = null;
                    var duration = 1200; // ms

                    function step(timestamp) {
                        if (!startTime) startTime = timestamp;
                        var progress = Math.min((timestamp - startTime) / duration, 1.0);
                        // Ease-out cubic: 1 - pow(1 - p, 3)
                        var ease = 1 - Math.pow(1 - progress, 3);
                        var current = (targetVal * ease).toFixed(decimals);

                        el.innerText = prefix + current + suffix;

                        if (progress < 1.0 && window.__isTabActive) {
                            requestAnimationFrame(step);
                        } else {
                            el.innerText = rawText; // Ensure exact target formatting
                        }
                    }

                    requestAnimationFrame(step);
                }
            });
        }, { threshold: 0.15 });

        counterElements.forEach(function(el) {
            observer.observe(el);
        });
    }

    // 4. Staggered Scroll & Section Entrance Reveals
    function initScrollReveals() {
        var elements = document.querySelectorAll('.eoc-animate-in, .eoc-stagger-item');
        if (!elements || elements.length === 0) return;

        if (prefersReducedMotion) {
            elements.forEach(function(el) { el.style.opacity = '1'; });
            return;
        }

        var observer = new IntersectionObserver(function(entries) {
            entries.forEach(function(entry) {
                if (entry.isIntersecting) {
                    entry.target.classList.add('eoc-page-enter');
                }
            });
        }, { threshold: 0.08 });

        elements.forEach(function(el) {
            observer.observe(el);
        });
    }

    // 5. Interactive Tactical Incident Submission Processing Pipeline Overlay
    window.launchSubmissionPipeline = function(options) {
        options = options || {};
        var stages = options.stages || [
            { id: 1, title: 'Field Evidence Ingestion', sub: 'Packaging incident narrative, photographic asset & GPS telemetry' },
            { id: 2, title: 'Multimodal Neural Classification', sub: 'TF-IDF Vectorizer + 2D-CNN & Gemini 2.5 Flash Vision' },
            { id: 3, title: 'Composite Trust Metric Computation', sub: 'Calibrating Cryptographic, DL Confidence & Vision weights' },
            { id: 4, title: 'Decentralized Blockchain Anchoring', sub: 'Executing Web3 RPC transaction to Ethereum Devnet Contract' },
            { id: 5, title: 'Ledger State Confirmation', sub: 'Immutable SHA-256 state proof committed' }
        ];

        var existing = document.getElementById('eocPipelineOverlay');
        if (existing) existing.remove();

        var overlay = document.createElement('div');
        overlay.id = 'eocPipelineOverlay';
        overlay.className = 'pipeline-overlay active';

        var stepsHtml = stages.map(function(st, idx) {
            return '<div class="pipeline-step" id="pipelineStep_' + (idx + 1) + '">' +
                '<div class="pipeline-step-badge">' + (idx + 1) + '</div>' +
                '<div>' +
                    '<div style="font-size: 13px; font-weight: 700; color: #F1F5F9;">' + st.title + '</div>' +
                    '<div style="font-size: 11px; color: #94A3B8; margin-top: 2px;">' + st.sub + '</div>' +
                '</div>' +
            '</div>';
        }).join('');

        overlay.innerHTML = 
            '<div class="pipeline-dialog">' +
                '<div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 18px; border-bottom: 1px solid #26364C; padding-bottom: 12px;">' +
                    '<div style="display: flex; align-items: center; gap: 8px;">' +
                        '<div class="tactical-beacon">' +
                            '<div class="tactical-beacon-dot"></div>' +
                            '<div class="tactical-beacon-ring"></div>' +
                        '</div>' +
                        '<span style="font-size: 14px; font-weight: 800; color: #22D3EE; text-transform: uppercase; letter-spacing: 0.6px;">' + (options.title || 'Anchoring Incident Record') + '</span>' +
                    '</div>' +
                    '<span style="font-size: 10px; font-family: monospace; color: #64748B;">PROTOCOL v2.5</span>' +
                '</div>' +
                '<div id="pipelineStepsContainer">' + stepsHtml + '</div>' +
                '<div style="margin-top: 18px; text-align: center; font-size: 11px; color: #64748B; font-family: monospace;">' +
                    'Connecting to Truffle Devnet &bull; Smart Contract RPC' +
                '</div>' +
            '</div>';

        document.body.appendChild(overlay);

        // Sequence steps
        var current = 1;
        function advance() {
            var stepEl = document.getElementById('pipelineStep_' + current);
            if (stepEl) {
                stepEl.classList.add('active');
                if (current > 1) {
                    var prev = document.getElementById('pipelineStep_' + (current - 1));
                    if (prev) {
                        prev.classList.remove('active');
                        prev.classList.add('completed');
                        var b = prev.querySelector('.pipeline-step-badge');
                        if (b) b.innerHTML = '&#10004;';
                    }
                }
            }
            if (current < stages.length) {
                current++;
                setTimeout(advance, 650);
            }
        }
        advance();
    };

    // Auto-initialize on DOM ready
    function initAll() {
        initCardTilt3D();
        initCounterAnimations();
        initScrollReveals();
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initAll);
    } else {
        initAll();
    }

    window.initTacticalMotion = initAll;
})();

