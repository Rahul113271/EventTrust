/**
 * EventTrust (TrustChain v2.5) — Tactical Ambient 3D Constellation Mesh
 * Ultra-Lightweight, High-Performance Background Visualization
 */

(function() {
    'use strict';

    function initTacticalAmbient3D(canvasId) {
        if (window.__ambient3DActive) return;

        if (typeof THREE === 'undefined') {
            console.warn('[Ambient3D] Three.js not loaded. Skipping ambient background.');
            return;
        }

        var container = document.getElementById(canvasId || 'tactical-ambient-canvas');
        if (!container) {
            container = document.createElement('div');
            container.id = 'tactical-ambient-canvas';
            container.style.position = 'fixed';
            container.style.inset = '0';
            container.style.pointerEvents = 'none';
            container.style.zIndex = '0';
            container.style.opacity = '0.35';
            document.body.insertBefore(container, document.body.firstChild);
        }

        window.__ambient3DActive = true;

        var width = window.innerWidth;
        var height = window.innerHeight;

        var scene = new THREE.Scene();
        var camera = new THREE.PerspectiveCamera(50, width / height, 0.1, 1000);
        camera.position.z = 40;

        var renderer = new THREE.WebGLRenderer({ antialias: false, alpha: true, powerPreference: 'low-power' });
        renderer.setSize(width, height);
        renderer.setPixelRatio(1);
        container.appendChild(renderer.domElement);

        var group = new THREE.Group();
        scene.add(group);

        // Peripheral Node Constellation
        var nodeCount = 42;
        var nodes = [];
        var nodeGeo = new THREE.SphereGeometry(0.28, 8, 8);
        var nodeMat = new THREE.MeshBasicMaterial({ color: 0x22D3EE, transparent: true, opacity: 0.7 });

        for (var i = 0; i < nodeCount; i++) {
            var mesh = new THREE.Mesh(nodeGeo, nodeMat);
            // Distribute primarily to edges / peripherals
            var angle = Math.random() * Math.PI * 2;
            var radius = 16 + Math.random() * 26;
            var x = Math.cos(angle) * radius;
            var y = (Math.random() - 0.5) * 36;
            var z = (Math.random() - 0.5) * 20;

            mesh.position.set(x, y, z);
            group.add(mesh);
            nodes.push({
                mesh: mesh,
                vx: (Math.random() - 0.5) * 0.015,
                vy: (Math.random() - 0.5) * 0.015,
                vz: (Math.random() - 0.5) * 0.01
            });
        }

        // Connecting lines between nearby nodes
        var maxDistance = 14;
        var lineGeo = new THREE.BufferGeometry();
        var lineMat = new THREE.LineBasicMaterial({ color: 0x1E3A5F, transparent: true, opacity: 0.28 });
        var lineMesh = new THREE.LineSegments(lineGeo, lineMat);
        group.add(lineMesh);

        var mouseX = 0, mouseY = 0;
        var targetX = 0, targetY = 0;

        function onMouseMove(e) {
            mouseX = (e.clientX / width - 0.5) * 0.3;
            mouseY = (e.clientY / height - 0.5) * 0.3;
        }
        window.addEventListener('mousemove', onMouseMove, { passive: true });

        var clock = new THREE.Clock();

        function animate() {
            if (window.__isTabActive) {
                var elapsed = clock.getElapsedTime();

                targetX += (mouseX - targetX) * 0.02;
                targetY += (mouseY - targetY) * 0.02;

                group.rotation.y = targetX + elapsed * 0.02;
                group.rotation.x = -targetY + Math.sin(elapsed * 0.04) * 0.03;

                // Update node positions
                var linePositions = [];
                for (var i = 0; i < nodes.length; i++) {
                    var n = nodes[i];
                    n.mesh.position.x += n.vx;
                    n.mesh.position.y += n.vy;
                    n.mesh.position.z += n.vz;

                    // Bounds bounce
                    if (Math.abs(n.mesh.position.x) > 34) n.vx *= -1;
                    if (Math.abs(n.mesh.position.y) > 22) n.vy *= -1;
                    if (Math.abs(n.mesh.position.z) > 15) n.vz *= -1;

                    // Check neighbors
                    for (var j = i + 1; j < nodes.length; j++) {
                        var n2 = nodes[j];
                        var dist = n.mesh.position.distanceTo(n2.mesh.position);
                        if (dist < maxDistance) {
                            linePositions.push(
                                n.mesh.position.x, n.mesh.position.y, n.mesh.position.z,
                                n2.mesh.position.x, n2.mesh.position.y, n2.mesh.position.z
                            );
                        }
                    }
                }

                lineGeo.setAttribute('position', new THREE.Float32BufferAttribute(linePositions, 3));

                renderer.render(scene, camera);
            }
            requestAnimationFrame(animate);
        }

        animate();

        window.addEventListener('resize', function() {
            width = window.innerWidth;
            height = window.innerHeight;
            camera.aspect = width / height;
            camera.updateProjectionMatrix();
            renderer.setSize(width, height);
        }, { passive: true });
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', function() { initTacticalAmbient3D(); });
    } else {
        initTacticalAmbient3D();
    }

    window.initTacticalAmbient3D = initTacticalAmbient3D;
})();

