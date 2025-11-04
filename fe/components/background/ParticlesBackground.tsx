import {useEffect, useRef} from "react";

export default function ParticlesBackground() {
    const ref = useRef<HTMLCanvasElement>(null)

  useEffect(() => {
    const canvas = ref.current
    if (!canvas) return

    const ctx = canvas.getContext("2d")!
    let w = (canvas.width = window.innerWidth)
    let h = (canvas.height = window.innerHeight)

    const particles = Array.from({ length: 50 }).map(() => ({
      x: Math.random() * w,
      y: Math.random() * h,
      vx: (Math.random() - 0.5) * 0.8,
      vy: (Math.random() - 0.5) * 0.8,
      r: 1 + Math.random() * 4,
      alpha: 0.1 + Math.random() * 0.4,
      color: Math.random() < 0.3 ? "#811CD0" : Math.random() < 0.6 ? "#CE1C5B" : "#23CCBE",
      pulse: Math.random() * Math.PI * 2,
      pulseSpeed: 0.02 + Math.random() * 0.03,
    }))

    const orbs = Array.from({ length: 8 }).map(() => ({
      x: Math.random() * w,
      y: Math.random() * h,
      vx: (Math.random() - 0.5) * 0.3,
      vy: (Math.random() - 0.5) * 0.3,
      r: 20 + Math.random() * 40,
      alpha: 0.05 + Math.random() * 0.1,
      color: ["#811CD0", "#CE1C5B", "#23CCBE"][Math.floor(Math.random() * 3)],
      pulse: Math.random() * Math.PI * 2,
      pulseSpeed: 0.01 + Math.random() * 0.02,
    }))

    let time = 0

    function draw() {
      time += 0.016

      const gradient = ctx.createLinearGradient(0, 0, w, h)
      gradient.addColorStop(0, "#1a0b2e")
      gradient.addColorStop(0.3, "#16213e")
      gradient.addColorStop(0.7, "#0f3460")
      gradient.addColorStop(1, "#533483")
      ctx.fillStyle = gradient
      ctx.fillRect(0, 0, w, h)

      orbs.forEach((orb) => {
        orb.x += orb.vx
        orb.y += orb.vy
        orb.pulse += orb.pulseSpeed

        if (orb.x < -orb.r) orb.x = w + orb.r
        if (orb.x > w + orb.r) orb.x = -orb.r
        if (orb.y < -orb.r) orb.y = h + orb.r
        if (orb.y > h + orb.r) orb.y = -orb.r

        const pulseFactor = 1 + Math.sin(orb.pulse) * 0.3
        const currentR = orb.r * pulseFactor
        const currentAlpha = orb.alpha * (1 + Math.sin(orb.pulse) * 0.5)

        const orbGradient = ctx.createRadialGradient(orb.x, orb.y, 0, orb.x, orb.y, currentR)
        orbGradient.addColorStop(
          0,
          orb.color +
            Math.floor(currentAlpha * 255)
              .toString(16)
              .padStart(2, "0"),
        )
        orbGradient.addColorStop(1, orb.color + "00")

        ctx.beginPath()
        ctx.arc(orb.x, orb.y, currentR, 0, Math.PI * 2)
        ctx.fillStyle = orbGradient
        ctx.fill()
      })

      particles.forEach((p) => {
        p.x += p.vx + Math.sin(time + p.pulse) * 0.5
        p.y += p.vy + Math.cos(time + p.pulse) * 0.3
        p.pulse += p.pulseSpeed

        if (p.x < 0) p.x = w
        if (p.x > w) p.x = 0
        if (p.y < 0) p.y = h
        if (p.y > h) p.y = 0

        const pulseFactor = 1 + Math.sin(p.pulse) * 0.5
        const currentR = p.r * pulseFactor
        const currentAlpha = p.alpha * (1 + Math.sin(p.pulse + time) * 0.3)

        ctx.beginPath()
        ctx.arc(p.x, p.y, currentR, 0, Math.PI * 2)
        ctx.fillStyle =
          p.color +
          Math.floor(currentAlpha * 255)
            .toString(16)
            .padStart(2, "0")
        ctx.fill()
      })

      requestAnimationFrame(draw)
    }

    draw()

    const onResize = () => {
      w = canvas.width = window.innerWidth
      h = canvas.height = window.innerHeight
    }

    window.addEventListener("resize", onResize)
    return () => window.removeEventListener("resize", onResize)
  }, [])

  return (
    <canvas
      ref={ref}
      className="absolute inset-0"
      style={{
        zIndex: 0,
        background: "linear-gradient(135deg, #1a0b2e 0%, #16213e 30%, #0f3460 70%, #533483 100%)",
      }}
    />
  )
}