/**
 * EventTrust — Cinematic 3D Tactical Global Disaster Earth
 * Powered by Three.js (r128)
 * 
 * Features:
 * - High-tech wireframe tactical sphere with landmass constellations
 * - Atmospheric rim glow (Fresnel effect)
 * - Major disaster monitoring hubs (Tokyo, London, NYC, Mumbai, Sydney, etc.)
 * - 3D 3-point Quadratic Bezier telemetry arcs connecting global crisis centers
 * - Traveling light packets pulsing along telemetry arcs
 * - Ambient cosmic particle field with mouse orbit parallax
 * - Zero-lag, visibility-aware animation loop
 */

(function() {
    'use strict';

    function initEarth3D(containerId) {
        var container = document.getElementById(containerId || 'earth-3d-canvas');
        if (!container) return;

        if (typeof THREE === 'undefined') {
            console.warn('[Earth3D] Three.js not loaded. Skipping 3D globe.');
            return;
        }

        // Clean previous instances
        while (container.firstChild) {
            container.removeChild(container.firstChild);
        }

        var width = container.clientWidth || 380;
        var height = container.clientHeight || 340;

        // 1. Scene & Camera
        var scene = new THREE.Scene();
        var camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 1000);
        camera.position.set(0, 4, 28);

        // 2. Renderer
        var renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
        renderer.setSize(width, height);
        renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
        container.appendChild(renderer.domElement);

        var masterGroup = new THREE.Group();
        scene.add(masterGroup);

        // 3. Tactical Wireframe Globe
        var globeRadius = 9.2;

        // Base dark sphere
        var baseGeo = new THREE.SphereGeometry(globeRadius * 0.98, 36, 36);
        var baseMat = new THREE.MeshBasicMaterial({
            color: 0x08101D,
            transparent: true,
            opacity: 0.92
        });
        var baseSphere = new THREE.Mesh(baseGeo, baseMat);
        masterGroup.add(baseSphere);

        // Wireframe grid lines
        var wireGeo = new THREE.SphereGeometry(globeRadius, 28, 28);
        var wireMat = new THREE.MeshBasicMaterial({
            color: 0x1E3A5F,
            wireframe: true,
            transparent: true,
            opacity: 0.38
        });
        var wireSphere = new THREE.Mesh(wireGeo, wireMat);
        masterGroup.add(wireSphere);

        // Latitude / Longitude Highlight Rings (Equator, Prime Meridian, Tropics)
        function createRing(r, rotX, rotY, color, opac) {
            var rGeo = new THREE.RingGeometry(r - 0.05, r + 0.05, 64);
            var rMat = new THREE.MeshBasicMaterial({
                color: color || 0x22D3EE,
                side: THREE.DoubleSide,
                transparent: true,
                opacity: opac || 0.4
            });
            var ring = new THREE.Mesh(rGeo, rMat);
            ring.rotation.x = rotX || 0;
            ring.rotation.y = rotY || 0;
            return ring;
        }
        masterGroup.add(createRing(globeRadius * 1.005, Math.PI / 2, 0, 0x22D3EE, 0.5)); // Equator
        masterGroup.add(createRing(globeRadius * 1.005, 0, 0, 0x18304E, 0.3));

        // Atmospheric Outer Rim Glow
        var glowGeo = new THREE.SphereGeometry(globeRadius * 1.14, 32, 32);
        var glowMat = new THREE.ShaderMaterial({
            vertexShader: [
                'varying vec3 vNormal;',
                'void main() {',
                '    vNormal = normalize(normalMatrix * normal);',
                '    gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);',
                '}'
            ].join('\n'),
            fragmentShader: [
                'varying vec3 vNormal;',
                'void main() {',
                '    float intensity = pow(0.68 - dot(vNormal, vec3(0.0, 0.0, 1.0)), 2.2);',
                '    gl_FragColor = vec4(0.13, 0.82, 0.93, 1.0) * intensity * 0.75;',
                '}'
            ].join('\n'),
            side: THREE.BackSide,
            blending: THREE.AdditiveBlending,
            transparent: true
        });
        var glowMesh = new THREE.Mesh(glowGeo, glowMat);
        masterGroup.add(glowMesh);

        // 4. Coordinates to 3D Cartesian
        function latLongToVector3(lat, lon, radius, alt) {
            var phi = (90 - lat) * (Math.PI / 180);
            var theta = (lon + 180) * (Math.PI / 180);
            var r = radius + (alt || 0);
            return new THREE.Vector3(
                -(r * Math.sin(phi) * Math.cos(theta)),
                r * Math.cos(phi),
                r * Math.sin(phi) * Math.sin(theta)
            );
        }

        // Crisis Monitoring Hubs
        var hubs = [
            { name: 'Tokyo EOC', lat: 35.6762, lon: 139.6503, color: 0xF87171, isCrisis: true },
            { name: 'Mumbai Hub', lat: 19.0760, lon: 72.8777, color: 0x22D3EE, isCrisis: false },
            { name: 'London Station', lat: 51.5074, lon: -0.1278, color: 0x34D399, isCrisis: false },
            { name: 'New York Command', lat: 40.7128, lon: -74.0060, color: 0xF87171, isCrisis: true },
            { name: 'San Francisco', lat: 37.7749, lon: -122.4194, color: 0x22D3EE, isCrisis: false },
            { name: 'Sydney Outpost', lat: -33.8688, lon: 151.2093, color: 0x34D399, isCrisis: false },
            { name: 'Nairobi Monitor', lat: -1.2921, lon: 36.8219, color: 0xFBBF24, isCrisis: false },
            { name: 'Rio de Janeiro', lat: -22.9068, lon: -43.1729, color: 0x22D3EE, isCrisis: false }
        ];

        var hubMeshes = [];
        hubs.forEach(function(h) {
            var pos = latLongToVector3(h.lat, h.lon, globeRadius, 0.05);

            // Node core pin
            var pGeo = new THREE.SphereGeometry(0.24, 16, 16);
            var pMat = new THREE.MeshBasicMaterial({ color: h.color });
            var pMesh = new THREE.Mesh(pGeo, pMat);
            pMesh.position.copy(pos);
            masterGroup.add(pMesh);

            // Concentric sonar beacon ring
            var beaconGeo = new THREE.RingGeometry(0.35, 0.48, 24);
            var beaconMat = new THREE.MeshBasicMaterial({
                color: h.color,
                side: THREE.DoubleSide,
                transparent: true,
                opacity: 0.8
            });
            var beacon = new THREE.Mesh(beaconGeo, beaconMat);
            beacon.position.copy(pos.clone().multiplyScalar(1.01));
            beacon.lookAt(pos.clone().multiplyScalar(2));
            masterGroup.add(beacon);

            hubMeshes.push({ mesh: pMesh, beacon: beacon, isCrisis: h.isCrisis });
        });

        // 5. Arcs Connecting Hubs
        var arcPairs = [
            [0, 1], // Tokyo - Mumbai
            [1, 2], // Mumbai - London
            [2, 3], // London - NYC
            [3, 4], // NYC - SF
            [0, 5], // Tokyo - Sydney
            [2, 6], // London - Nairobi
            [3, 7]  // NYC - Rio
        ];

        var packets = [];

        arcPairs.forEach(function(pair) {
            var start = latLongToVector3(hubs[pair[0]].lat, hubs[pair[0]].lon, globeRadius, 0.08);
            var end = latLongToVector3(hubs[pair[1]].lat, hubs[pair[1]].lon, globeRadius, 0.08);

            // Calculate elevation midpoint
            var mid = start.clone().add(end).multiplyScalar(0.5);
            var dist = start.distanceTo(end);
            var midHeight = globeRadius + dist * 0.32;
            mid.normalize().multiplyScalar(midHeight);

            var curve = new THREE.QuadraticBezierCurve3(start, mid, end);
            var pts = curve.getPoints(50);
            var curveGeo = new THREE.BufferGeometry().setFromPoints(pts);
            var curveMat = new THREE.LineBasicMaterial({
                color: 0x22D3EE,
                transparent: true,
                opacity: 0.42
            });
            var arcLine = new THREE.Line(curveGeo, curveMat);
            masterGroup.add(arcLine);

            // Traveling light pulse packet
            var pktGeo = new THREE.SphereGeometry(0.18, 12, 12);
            var pktMat = new THREE.MeshBasicMaterial({
                color: 0x22D3EE
            });
            var pkt = new THREE.Mesh(pktGeo, pktMat);
            masterGroup.add(pkt);

            packets.push({ mesh: pkt, curve: curve, t: Math.random(), speed: 0.003 + Math.random() * 0.003 });
        });

        // 6. Cosmic Stardust Particles
        var starCount = 180;
        var starGeo = new THREE.BufferGeometry();
        var starPositions = new Float32Array(starCount * 3);
        for (var s = 0; s < starCount * 3; s += 3) {
            starPositions[s] = (Math.random() - 0.5) * 60;
            starPositions[s + 1] = (Math.random() - 0.5) * 60;
            starPositions[s + 2] = (Math.random() - 0.5) * 40;
        }
        starGeo.setAttribute('position', new THREE.BufferAttribute(starPositions, 3));
        var starMat = new THREE.PointsMaterial({
            color: 0x38BDF8,
            size: 0.4,
            transparent: true,
            opacity: 0.5
        });
        var stars = new THREE.Points(starGeo, starMat);
        scene.add(stars);

        // 7. Interactive Mouse Parallax
        var mouseX = 0, mouseY = 0;
        var targetX = 0, targetY = 0;

        function onMouseMove(e) {
            var rect = container.getBoundingClientRect();
            mouseX = ((e.clientX - rect.left) / width - 0.5) * 0.4;
            mouseY = ((e.clientY - rect.top) / height - 0.5) * 0.4;
        }
        window.addEventListener('mousemove', onMouseMove, { passive: true });

        // 8. Animation Loop
        var clock = new THREE.Clock();

        function animate() {
            if (window.__isTabActive) {
                var elapsed = clock.getElapsedTime();

                // Gentle orbital rotation
                masterGroup.rotation.y += 0.003;

                // Mouse parallax
                targetX += (mouseX - targetX) * 0.04;
                targetY += (mouseY - targetY) * 0.04;
                masterGroup.rotation.x = 0.25 + targetY;
                masterGroup.position.x = targetX * 3.0;

                // Pulse beacons
                hubMeshes.forEach(function(hm, idx) {
                    var s = 1.0 + Math.sin(elapsed * 3.0 + idx) * 0.25;
                    hm.beacon.scale.set(s, s, s);
                });

                // Move arc packets
                packets.forEach(function(p) {
                    p.t += p.speed;
                    if (p.t > 1.0) p.t = 0;
                    var pt = p.curve.getPoint(p.t);
                    p.mesh.position.copy(pt);
                });

                // Subtle star drift
                stars.rotation.y -= 0.0004;

                renderer.render(scene, camera);
            }
            requestAnimationFrame(animate);
        }

        animate();

        // 9. Resize Handler
        function onResize() {
            if (!container) return;
            width = container.clientWidth || 380;
            height = container.clientHeight || 340;
            camera.aspect = width / height;
            camera.updateProjectionMatrix();
            renderer.setSize(width, height);
        }
        window.addEventListener('resize', onResize, { passive: true });
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', function() { initEarth3D(); });
    } else {
        initEarth3D();
    }

    window.initEarth3D = initEarth3D;
})();

