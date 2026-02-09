const canvas = document.getElementById("bg");
const ctx = canvas.getContext("2d");

let w, h;
function resize() {
  w = canvas.width = window.innerWidth;
  h = canvas.height = window.innerHeight;
}
resize();
window.addEventListener("resize", resize);

const bubbles = [];
const COUNT = 80;

for (let i = 0; i < COUNT; i++) {
  bubbles.push({
    x: Math.random() * w,
    y: Math.random() * h,
    r: Math.random() * 2 + 1,
    dx: (Math.random() - 0.5) * 0.6,
    dy: (Math.random() - 0.5) * 0.6
  });
}

function draw() {
  ctx.clearRect(0, 0, w, h);

  bubbles.forEach(b => {
    ctx.beginPath();
    ctx.arc(b.x, b.y, b.r, 0, Math.PI * 2);
    ctx.fillStyle = "rgba(56,189,248,0.35)";
    ctx.fill();

    b.x += b.dx;
    b.y += b.dy;

    if (b.x < 0 || b.x > w) b.dx *= -1;
    if (b.y < 0 || b.y > h) b.dy *= -1;
  });

  requestAnimationFrame(draw);
}
draw();

/* Mouse interaction (bubble push) */
window.addEventListener("mousemove", e => {
  bubbles.forEach(b => {
    const dist = Math.hypot(b.x - e.clientX, b.y - e.clientY);
    if (dist < 120) {
      b.x += (b.x - e.clientX) * 0.02;
      b.y += (b.y - e.clientY) * 0.02;
    }
  });
});
