/**
 * EventTrust (TrustChain v2.5) — 3D Cryptographic Blockchain Verification Visualizer
 * Powered by Three.js (r128)
 * 
 * Features:
 * - Floating connected Ethereum blockchain block lattice
 * - Active Target Block inspection with real-time on-chain status binding:
 *     * VERIFIED: Emerald crystal core (#34D399), solid cyan laser conduits, verified energy rings
 *     * TAMPERED: Fractured crimson wireframe (#F87171), severed red lasers, alert pulse
 *     * UNANCHORED: Amber hollow lattice (#FBBF24), pending link
 * - Interactive 3D mouse orbit & parallax
 * - High-speed cryptographic data transmission pulses
 * - Zero-lag, visibility-aware animation loop
 */

(function() {
    'use strict';

    function initBlockchainVerify3D(containerId, status, eventId) {
        var container = document.getElementById(containerId || 'blockchain-verify-canvas');
        if (!container) return;

        if (typeof THREE === 'undefined') {
            console.warn('[BlockchainVerify3D] Three.js not loaded. Skipping 3D visualizer.');
            return;
        }

        while (container.firstChild) {
            container.removeChild(container.firstChild);
        }

        var width = container.clientWidth || 800;
        var height = container.clientHeight || 280;

        // 1. Scene & Camera
        var scene = new THREE.Scene();
        var camera = new THREE.PerspectiveCamera(40, width / height, 0.1, 1000);
        camera.position.set(0, 1.8, 16);

        // 2. High-Performance WebGL Renderer
        var renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
        renderer.setSize(width, height);
        renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
        container.appendChild(renderer.domElement);

        var worldGroup = new THREE.Group();
        scene.add(worldGroup);

        // Status normalization
        var isVerified = (status === 'VERIFIED');
        var isTampered = (status && status.indexOf('TAMPERED') !== -1);
        var isUnanchored = (!isVerified && !isTampered);

        var activeColor = isVerified ? 0x34D399 : (isTampered ? 0xF87171 : 0xFBBF24);
        var wireColor = isVerified ? 0x22D3EE : (isTampered ? 0xEF4444 : 0xF59E0B);

        // 3. Chain of Blocks (-2, -1, 0 [Active], +1, +2)
        var blocks = [];
        var blockConfigs = [
            { idx: -2, label: 'Block #' + (eventId ? (parseInt(eventId) - 2) : '35'), x: -7.2, isTarget: false },
            { idx: -1, label: 'Block #' + (eventId ? (parseInt(eventId) - 1) : '36'), x: -3.6, isTarget: false },
            { idx: 0,  label: 'Block #' + (eventId ? eventId : '37') + ' (TARGET)', x: 0, isTarget: true },
            { idx: 1,  label: 'Block #' + (eventId ? (parseInt(eventId) + 1) : '38'), x: 3.6, isTarget: false },
            { idx: 2,  label: 'Pending #' + (eventId ? (parseInt(eventId) + 2) : '39'), x: 7.2, isTarget: false }
        ];

        var conduits = [];

        blockConfigs.forEach(function(cfg, i) {
            var bGroup = new THREE.Group();
            bGroup.position.set(cfg.x, 0, 0);

            var size = cfg.isTarget ? 1.55 : 1.15;

            // Outer wireframe cage
            var boxGeo = new THREE.BoxGeometry(size, size, size);
            var edgeGeo = new THREE.EdgesGeometry(boxGeo);
            var edgeMat = new THREE.LineBasicMaterial({
                color: cfg.isTarget ? activeColor : 0x26364C,
                linewidth: cfg.isTarget ? 2 : 1
            });
            var wireBox = new THREE.LineSegments(edgeGeo, edgeMat);
            bGroup.add(wireBox);

            // Inner solid translucent core
            var coreGeo = new THREE.BoxGeometry(size * 0.72, size * 0.72, size * 0.72);
            var coreMat = new THREE.MeshBasicMaterial({
                color: cfg.isTarget ? activeColor : 0x121C2E,
                transparent: true,
                opacity: cfg.isTarget ? (isTampered ? 0.85 : 0.65) : 0.4
            });
            var coreMesh = new THREE.Mesh(coreGeo, coreMat);
            bGroup.add(coreMesh);

            // Internal spinning cryptographic octahedron gem
            var gemGeo = new THREE.OctahedronGeometry(size * 0.38);
            var gemMat = new THREE.MeshBasicMaterial({
                color: cfg.isTarget ? activeColor : 0x22D3EE,
                wireframe: true
            });
            var gemMesh = new THREE.Mesh(gemGeo, gemMat);
            bGroup.add(gemMesh);

            // Orbiting verification energy ring for Target Block
            var ringMesh = null;
            if (cfg.isTarget && isVerified) {
                var rGeo = new THREE.RingGeometry(size * 1.05, size * 1.15, 32);
                var rMat = new THREE.MeshBasicMaterial({
                    color: 0x34D399,
                    side: THREE.DoubleSide,
                    transparent: true,
                    opacity: 0.75
                });
                ringMesh = new THREE.Mesh(rGeo, rMat);
                ringMesh.rotation.x = Math.PI / 2;
                bGroup.add(ringMesh);
            }

            worldGroup.add(bGroup);
            blocks.push({
                group: bGroup,
                gem: gemMesh,
                ring: ringMesh,
                wire: wireBox,
                isTarget: cfg.isTarget,
                baseY: 0,
                speed: 0.015 + Math.random() * 0.01
            });
        });

        // 4. Connecting Laser Conduits Between Blocks
        for (var c = 0; c < blockConfigs.length - 1; c++) {
            var b1 = blockConfigs[c];
            var b2 = blockConfigs[c + 1];

            var isSevered = (isTampered && (b1.isTarget || b2.isTarget));
            var conduitColor = isSevered ? 0xF87171 : (isVerified ? 0x22D3EE : 0x38BDF8);

            var lineGeo = new THREE.BufferGeometry().setFromPoints([
                new THREE.Vector3(b1.x + 0.8, 0, 0),
                new THREE.Vector3(b2.x - 0.8, 0, 0)
            ]);
            var lineMat = new THREE.LineDashedMaterial({
                color: conduitColor,
                dashSize: isSevered ? 0.2 : 0.4,
                gapSize: isSevered ? 0.3 : 0.15,
                transparent: true,
                opacity: isSevered ? 0.4 : 0.85
            });
            var line = new THREE.Line(lineGeo, lineMat);
            line.computeLineDistances();
            worldGroup.add(line);

            // High-speed laser data packet
            var pktGeo = new THREE.SphereGeometry(0.12, 10, 10);
            var pktMat = new THREE.MeshBasicMaterial({ color: isSevered ? 0xF87171 : 0x34D399 });
            var pkt = new THREE.Mesh(pktGeo, pktMat);
            worldGroup.add(pkt);

            conduits.push({
                line: line,
                packet: pkt,
                startX: b1.x + 0.8,
                endX: b2.x - 0.8,
                t: Math.random(),
                isSevered: isSevered
            });
        }

        // 5. Ambient Cryptographic Dust
        var pCount = 90;
        var pGeo = new THREE.BufferGeometry();
        var pPos = new Float32Array(pCount * 3);
        for (var p = 0; p < pCount * 3; p += 3) {
            pPos[p] = (Math.random() - 0.5) * 20;
            pPos[p + 1] = (Math.random() - 0.5) * 8;
            pPos[p + 2] = (Math.random() - 0.5) * 10;
        }
        pGeo.setAttribute('position', new THREE.BufferAttribute(pPos, 3));
        var pMat = new THREE.PointsMaterial({
            color: activeColor,
            size: 0.18,
            transparent: true,
            opacity: 0.45
        });
        var particles = new THREE.Points(pGeo, pMat);
        scene.add(particles);

        // 6. Interactive Mouse Orbit & Parallax
        var mouseX = 0, mouseY = 0;
        var targetX = 0, targetY = 0;

        function onMouseMove(e) {
            var rect = container.getBoundingClientRect();
            mouseX = ((e.clientX - rect.left) / width - 0.5) * 0.6;
            mouseY = ((e.clientY - rect.top) / height - 0.5) * 0.4;
        }
        window.addEventListener('mousemove', onMouseMove, { passive: true });

        // 7. Animation Loop
        var clock = new THREE.Clock();

        function animate() {
            if (window.__isTabActive) {
                var elapsed = clock.getElapsedTime();

                targetX += (mouseX - targetX) * 0.05;
                targetY += (mouseY - targetY) * 0.05;

                worldGroup.rotation.y = targetX * 0.8 + Math.sin(elapsed * 0.15) * 0.06;
                worldGroup.rotation.x = -targetY * 0.6 + 0.12;

                // Animate each block
                blocks.forEach(function(b, idx) {
                    b.group.position.y = b.baseY + Math.sin(elapsed * 1.5 + idx * 0.8) * (b.isTarget ? 0.18 : 0.10);
                    b.gem.rotation.x += b.speed;
                    b.gem.rotation.y += b.speed * 1.4;

                    if (b.ring) {
                        b.ring.rotation.z += 0.02;
                        var s = 1.0 + Math.sin(elapsed * 4.0) * 0.08;
                        b.ring.scale.set(s, s, s);
                    }

                    // Jitter for tampered block
                    if (b.isTarget && isTampered) {
                        b.group.position.x = (Math.random() - 0.5) * 0.06;
                        b.group.rotation.z = (Math.random() - 0.5) * 0.08;
                    }
                });

                // Animate data conduit packets
                conduits.forEach(function(c) {
                    if (!c.isSevered) {
                        c.t += 0.018;
                        if (c.t > 1.0) c.t = 0;
                        c.packet.position.set(
                            c.startX + (c.endX - c.startX) * c.t,
                            Math.sin(elapsed * 1.5) * 0.1,
                            0
                        );
                    } else {
                        // Erratic stutter for severed conduit
                        c.packet.position.set(
                            c.startX + (c.endX - c.startX) * 0.5 + (Math.random() - 0.5) * 0.2,
                            (Math.random() - 0.5) * 0.2,
                            0
                        );
                    }
                });

                particles.rotation.y -= 0.0006;

                renderer.render(scene, camera);
            }
            requestAnimationFrame(animate);
        }

        animate();

        // 8. Resize Handler
        function onResize() {
            if (!container) return;
            width = container.clientWidth || 800;
            height = container.clientHeight || 280;
            camera.aspect = width / height;
            camera.updateProjectionMatrix();
            renderer.setSize(width, height);
        }
        window.addEventListener('resize', onResize, { passive: true });
    }

    window.initBlockchainVerify3D = initBlockchainVerify3D;
})();

