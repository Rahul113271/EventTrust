/**
 * TrustChain — Ambient 3D Decentralized Ledger Mesh Background
 * Professional Web3 / Enterprise Cybersecurity 3D Lattice
 * 
 * Design Features:
 * - Peripheral & deep-space node distribution: zero clutter in the central reading corridor
 * - Micro-architectural wireframe block nodes with pulsating cryptographic jewel cores
 * - Ambient laser mesh ledger connections
 * - Subtle cosmic cryptographic dust particle field
 * - Gentle ambient sway & cursor parallax tilt
 */

(function() {
    function initFullscreenBlockchain3D() {
        if (window.__blockchain3DInitialized) return;

        if (typeof THREE === 'undefined') {
            console.warn("[TrustChain 3D] Three.js not loaded. Skipping 3D background.");
            return;
        }

        var container = document.getElementById('blockchain-bg-canvas');
        if (!container) {
            container = document.createElement('div');
            container.id = 'blockchain-bg-canvas';
            document.body.insertBefore(container, document.body.firstChild);
        }

        window.__blockchain3DInitialized = true;

        var width = window.innerWidth;
        var height = window.innerHeight;

        // 1. Scene, Camera, High-Performance WebGL Renderer
        var scene = new THREE.Scene();
        var camera = new THREE.PerspectiveCamera(48, width / height, 0.1, 1000);
        camera.position.set(0, 0, 36);

        var renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true, powerPreference: 'high-performance' });
        renderer.setSize(width, height);
        renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
        renderer.domElement.style.position = 'fixed';
        renderer.domElement.style.top = '0';
        renderer.domElement.style.left = '0';
        renderer.domElement.style.width = '100vw';
        renderer.domElement.style.height = '100vh';
        renderer.domElement.style.zIndex = '0';
        renderer.domElement.style.pointerEvents = 'none';
        container.appendChild(renderer.domElement);

        // 2. Atmospheric Lighting
        var ambientLight = new THREE.AmbientLight(0x0a1628, 2.0);
        scene.add(ambientLight);

        var lightCyan = new THREE.PointLight(0x00f2fe, 3.5, 90);
        lightCyan.position.set(-22, 14, 12);
        scene.add(lightCyan);

        var lightBlue = new THREE.PointLight(0x3b82f6, 3.5, 90);
        lightBlue.position.set(22, -12, 12);
        scene.add(lightBlue);

        var lightPurple = new THREE.PointLight(0x8b5cf6, 2.5, 80);
        lightPurple.position.set(0, 18, -10);
        scene.add(lightPurple);

        // Master Group
        var masterGroup = new THREE.Group();
        scene.add(masterGroup);

        // 3. Decentralized Node Distribution
        // IMPORTANT: Center corridor (|x| < 14, |y| < 12 in foreground) is intentionally kept free of foreground nodes
        // so typography, buttons, and cards remain 100% crisp, readable, and uncluttered.
        var nodePositions = [
            // Left flank cluster
            [-22, 11, -4],
            [-26, 4, 1],
            [-19, -2, 3],
            [-24, -9, -2],
            [-17, -13, 0],
            [-29, 13, -7],
            [-28, -6, 2],

            // Right flank cluster
            [22, 10, -4],
            [26, 3, 1],
            [19, -3, 3],
            [24, -10, -2],
            [17, -14, 0],
            [29, 12, -7],
            [28, -5, 2],

            // High orbital perimeter (pushed higher and deeper to keep topbar navigation completely clear)
            [-14, 21, -12],
            [14, 20, -12],
            [0, 24, -18],

            // Lower perimeter
            [-10, -18, -8],
            [10, -19, -8],

            // Deep background stratum (far behind content, subtle and atmospheric)
            [-7, 5, -28],
            [7, 4, -30],
            [-5, -6, -26],
            [6, -7, -28],
            [0, 9, -32]
        ];

        var nodes = [];
        var boxGeo = new THREE.BoxGeometry(1.25, 1.25, 1.25);
        var edgeGeo = new THREE.EdgesGeometry(boxGeo);

        for (var i = 0; i < nodePositions.length; i++) {
            var nodeGroup = new THREE.Group();
            var pos = nodePositions[i];
            nodeGroup.position.set(pos[0], pos[1], pos[2]);

            var isDeep = pos[2] < -20;
            var nodeColor = (i % 3 === 0) ? 0x00f2fe : (i % 3 === 1) ? 0x3b82f6 : 0x8b5cf6;

            // Wireframe Block Cube
            var edgeMat = new THREE.LineBasicMaterial({
                color: nodeColor,
                transparent: true,
                opacity: isDeep ? 0.35 : 0.65
            });
            var wireBox = new THREE.LineSegments(edgeGeo, edgeMat);
            nodeGroup.add(wireBox);

            // Inner Pulsating Octahedron Core
            var coreGeo = new THREE.OctahedronGeometry(isDeep ? 0.45 : 0.6, 0);
            var coreMat = new THREE.MeshPhongMaterial({
                color: (i % 2 === 0) ? 0x00f2fe : 0x3b82f6,
                emissive: (i % 2 === 0) ? 0x003344 : 0x111e38,
                shininess: 90,
                transparent: true,
                opacity: isDeep ? 0.45 : 0.75
            });
            var coreMesh = new THREE.Mesh(coreGeo, coreMat);
            nodeGroup.add(coreMesh);

            masterGroup.add(nodeGroup);
            nodes.push({
                group: nodeGroup,
                core: coreMesh,
                basePos: pos,
                rotSpeedX: 0.005 + (i * 0.0009) % 0.008,
                rotSpeedY: 0.006 + (i * 0.0011) % 0.008,
                floatSpeed: 0.9 + (i * 0.12) % 0.8,
                floatAmp: isDeep ? 0.2 : 0.35
            });
        }

        // 4. Interconnecting Ledger Streams
        var lineMat = new THREE.LineBasicMaterial({
            color: 0x00f2fe,
            transparent: true,
            opacity: 0.16
        });

        for (var a = 0; a < nodes.length; a++) {
            for (var b = a + 1; b < nodes.length; b++) {
                var p1 = nodes[a].group.position;
                var p2 = nodes[b].group.position;
                var dist = p1.distanceTo(p2);
                // Connect neighboring cluster nodes without crossing through the center reading corridor
                if (dist < 10.5 && !((p1.x < -5 && p2.x > 5) || (p1.x > 5 && p2.x < -5))) {
                    var lineGeo = new THREE.BufferGeometry().setFromPoints([p1, p2]);
                    var link = new THREE.Line(lineGeo, lineMat);
                    masterGroup.add(link);
                }
            }
        }

        // 5. Cryptographic Dust Particle Field (dispersed mainly towards outer radii)
        var particleCount = 420;
        var particleGeo = new THREE.BufferGeometry();
        var particlePositions = new Float32Array(particleCount * 3);

        for (var p = 0; p < particleCount * 3; p += 3) {
            var angle = Math.random() * Math.PI * 2;
            var radius = 12 + Math.random() * 26; // Keeps center clearer
            particlePositions[p] = Math.cos(angle) * radius;
            particlePositions[p + 1] = Math.sin(angle) * (radius * 0.7);
            particlePositions[p + 2] = (Math.random() - 0.5) * 36;
        }

        particleGeo.setAttribute('position', new THREE.BufferAttribute(particlePositions, 3));
        var particleMat = new THREE.PointsMaterial({
            color: 0x00f2fe,
            size: 0.16,
            transparent: true,
            opacity: 0.45
        });
        var particleSystem = new THREE.Points(particleGeo, particleMat);
        masterGroup.add(particleSystem);

        // 6. Smooth Mouse Parallax Tilt
        var mouseX = 0, mouseY = 0;
        var targetX = 0, targetY = 0;
        var windowHalfX = window.innerWidth / 2;
        var windowHalfY = window.innerHeight / 2;

        window.addEventListener('mousemove', function(e) {
            mouseX = (e.clientX - windowHalfX) * 0.00045;
            mouseY = (e.clientY - windowHalfY) * 0.00045;
        }, { passive: true });

        // Responsive Resize
        window.addEventListener('resize', function() {
            width = window.innerWidth;
            height = window.innerHeight;
            windowHalfX = width / 2;
            windowHalfY = height / 2;
            camera.aspect = width / height;
            camera.updateProjectionMatrix();
            renderer.setSize(width, height);
        }, { passive: true });

        // 7. Animation Loop — Elegant Sway, No Sweeping Occlusion
        var clock = new THREE.Clock();

        function animate() {
            requestAnimationFrame(animate);

            var elapsed = clock.getElapsedTime();

            targetX += (mouseX - targetX) * 0.035;
            targetY += (mouseY - targetY) * 0.035;

            // Gentle ambient sway (keeps constellations gracefully in their zones)
            masterGroup.rotation.y = Math.sin(elapsed * 0.07) * 0.05 + targetX;
            masterGroup.rotation.x = Math.sin(elapsed * 0.05) * 0.04 + targetY;

            // Individual node animations
            for (var i = 0; i < nodes.length; i++) {
                var nd = nodes[i];
                nd.group.rotation.x += nd.rotSpeedX;
                nd.group.rotation.y += nd.rotSpeedY;
                nd.core.rotation.y -= 0.015;
                nd.group.position.y = nd.basePos[1] + Math.sin(elapsed * nd.floatSpeed + i) * nd.floatAmp;
            }

            // Subtle particle drift
            particleSystem.rotation.y -= 0.0003;

            renderer.render(scene, camera);
        }

        animate();
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initFullscreenBlockchain3D);
    } else {
        initFullscreenBlockchain3D();
    }

    window.initFullscreenBlockchain3D = initFullscreenBlockchain3D;
})();
