/**
 * CYBERTEC8 - ADVANCED CURSOR SYSTEM
 * Optimized movement with linear interpolation (Lerp)
 */

document.addEventListener('DOMContentLoaded', () => {
    const system = document.querySelector('.cursor-system');
    const dot = document.querySelector('.cursor-dot');
    const outline = document.querySelector('.cursor-outline');
    const trailContainer = document.querySelector('.cursor-trail-container');

    let mouseX = 0, mouseY = 0;     // Actual mouse position
    let dotX = 0, dotY = 0;         // Dot position (no delay)
    let outlineX = 0, outlineY = 0; // Outline position (smooth delay)

    // Trail logic
    const trails = [];
    const trailCount = 8;
    for (let i = 0; i < trailCount; i++) {
        const t = document.createElement('div');
        t.className = 'cursor-trail';
        trailContainer.appendChild(t);
        trails.push({ el: t, x: 0, y: 0 });
    }

    // Capture mouse movement
    document.addEventListener('mousemove', (e) => {
        mouseX = e.clientX;
        mouseY = e.clientY;

        // Show cursor on first movement
        if (system.style.opacity === '0' || !system.style.opacity) {
            system.style.opacity = '1';
        }
    });

    // Interaction states
    document.addEventListener('mouseover', (e) => {
        if (e.target.closest('a, button, .btn-cyber, .nav-link, input, select, textarea')) {
            system.classList.add('hovering');
        }
    });

    document.addEventListener('mouseout', (e) => {
        if (e.target.closest('a, button, .btn-cyber, .nav-link, input, select, textarea')) {
            system.classList.remove('hovering');
        }
    });

    document.addEventListener('mousedown', () => system.classList.add('clicking'));
    document.addEventListener('mouseup', () => system.classList.remove('clicking'));
    document.addEventListener('mouseleave', () => system.style.opacity = '0');
    document.addEventListener('mouseenter', () => system.style.opacity = '1');

    // Animation loop (RAF)
    function animate() {
        // Dot follows instantly (or very slightly smoothed)
        dotX += (mouseX - dotX) * 0.8;
        dotY += (mouseY - dotY) * 0.8;
        dot.style.left = `${dotX}px`;
        dot.style.top = `${dotY}px`;

        // Outline follows with more delay (Lerp)
        outlineX += (mouseX - outlineX) * 0.15;
        outlineY += (mouseY - outlineY) * 0.15;
        outline.style.left = `${outlineX}px`;
        outline.style.top = `${outlineY}px`;

        // Trail follows with cascading delay
        let prevX = dotX;
        let prevY = dotY;

        trails.forEach((trail, index) => {
            trail.x += (prevX - trail.x) * 0.4;
            trail.y += (prevY - trail.y) * 0.4;
            trail.el.style.left = `${trail.x}px`;
            trail.el.style.top = `${trail.y}px`;

            // Fade out trail elements
            const scale = 1 - (index / trailCount);
            trail.el.style.transform = `translate(-50%, -50%) scale(${scale})`;
            trail.el.style.opacity = (0.4 * scale).toString();

            prevX = trail.x;
            prevY = trail.y;
        });

        requestAnimationFrame(animate);
    }

    // Initial opacity
    system.style.opacity = '0';

    // Start animation
    animate();
});
