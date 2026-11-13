<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref, watch } from 'vue'
import * as THREE from 'three'
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js'
import { buildGalaxy, mulberry32 } from '@/lib/galaxy'
import GalaxyCanvas from './GalaxyCanvas.vue'
import type { GalaxySkillStar } from '@/types/galaxy'

const props = defineProps<{
  skills: GalaxySkillStar[]
  progress: number
  active: boolean
}>()

const host = ref<HTMLElement | null>(null)
const failed = ref(false)

const SCALE = 5.2
const TAU = Math.PI * 2

let renderer: THREE.WebGLRenderer | null = null
let scene: THREE.Scene | null = null
let camera: THREE.PerspectiveCamera | null = null
let controls: OrbitControls | null = null
let root: THREE.Group | null = null
let frame = 0
let observer: ResizeObserver | null = null
let reduced = false
let lastTime = 0
let starTexture: THREE.CanvasTexture | null = null
let glowTexture: THREE.CanvasTexture | null = null
let progressMesh: THREE.Mesh | null = null

function makeRadialTexture(stops: [number, string][], size = 64): THREE.CanvasTexture {
  const canvas = document.createElement('canvas')
  canvas.width = size
  canvas.height = size
  const context = canvas.getContext('2d')
  if (context) {
    const gradient = context.createRadialGradient(
      size / 2,
      size / 2,
      0,
      size / 2,
      size / 2,
      size / 2,
    )
    for (const [offset, color] of stops) gradient.addColorStop(offset, color)
    context.fillStyle = gradient
    context.fillRect(0, 0, size, size)
  }
  return new THREE.CanvasTexture(canvas)
}

function disposeObject(object: THREE.Object3D): void {
  object.traverse((child) => {
    const mesh = child as THREE.Mesh
    mesh.geometry?.dispose()
    const material = mesh.material
    if (Array.isArray(material)) {
      material.forEach((item) => item.dispose())
    } else if (material) {
      material.dispose()
    }
  })
}

function clearRoot(): void {
  if (!root) return
  for (const child of [...root.children]) {
    root.remove(child)
    disposeObject(child)
  }
}

function resize(): void {
  const element = host.value
  if (!element || !renderer || !camera) return
  const width = element.clientWidth
  const height = element.clientHeight
  if (width === 0 || height === 0) return
  renderer.setSize(width, height, false)
  camera.aspect = width / height
  camera.updateProjectionMatrix()
}

function buildStarfield(): void {
  if (!scene || !starTexture) return
  const count = 1400
  const positions = new Float32Array(count * 3)
  const colors = new Float32Array(count * 3)
  const random = mulberry32(20261113)

  for (let index = 0; index < count; index += 1) {
    const radius = 4 + random() * 14
    const angle = random() * TAU
    positions[index * 3] = Math.cos(angle) * radius
    positions[index * 3 + 1] = (random() - 0.5) * 4
    positions[index * 3 + 2] = Math.sin(angle) * radius

    const warm = random() > 0.86
    const color = new THREE.Color(warm ? 0xffd0a0 : 0x8fa8c8)
    const intensity = 0.22 + random() * 0.55
    colors[index * 3] = color.r * intensity
    colors[index * 3 + 1] = color.g * intensity
    colors[index * 3 + 2] = color.b * intensity
  }

  const geometry = new THREE.BufferGeometry()
  geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3))
  geometry.setAttribute('color', new THREE.BufferAttribute(colors, 3))
  const material = new THREE.PointsMaterial({
    size: 0.09,
    map: starTexture,
    vertexColors: true,
    transparent: true,
    opacity: 0.8,
    depthWrite: false,
    blending: THREE.AdditiveBlending,
    sizeAttenuation: true,
  })
  scene.add(new THREE.Points(geometry, material))
}

function buildCore(): void {
  if (!scene || !glowTexture) return

  const sphere = new THREE.Mesh(
    new THREE.SphereGeometry(0.28, 24, 24),
    new THREE.MeshBasicMaterial({ color: 0xffc08a, toneMapped: false }),
  )
  scene.add(sphere)

  const sprite = new THREE.Sprite(
    new THREE.SpriteMaterial({
      map: glowTexture,
      color: 0xffa860,
      transparent: true,
      opacity: 0.8,
      depthWrite: false,
      blending: THREE.AdditiveBlending,
    }),
  )
  sprite.scale.set(3.2, 3.2, 1)
  scene.add(sprite)

  const guide = new THREE.Mesh(
    new THREE.RingGeometry(0.82, 0.95, 96),
    new THREE.MeshBasicMaterial({
      color: 0x8a5a3c,
      transparent: true,
      opacity: 0.16,
      side: THREE.DoubleSide,
      toneMapped: false,
    }),
  )
  guide.rotation.x = -Math.PI / 2
  guide.position.y = 0.01
  scene.add(guide)
}

function buildSceneContent(): void {
  if (!root) return
  clearRoot()
  const layout = buildGalaxy(props.skills)

  for (const ring of layout.rings) {
    const points: THREE.Vector3[] = []
    const segments = 128
    for (let index = 0; index <= segments; index += 1) {
      const angle = (index / segments) * TAU
      points.push(
        new THREE.Vector3(
          Math.cos(angle) * ring * SCALE,
          0,
          Math.sin(angle) * ring * SCALE,
        ),
      )
    }
    const geometry = new THREE.BufferGeometry().setFromPoints(points)
    const material = new THREE.LineBasicMaterial({
      color: 0x2b3547,
      transparent: true,
      opacity: 0.55,
    })
    root.add(new THREE.Line(geometry, material))
  }

  const nodeGeometry = new THREE.OctahedronGeometry(1, 0)
  const nodeMaterial = new THREE.MeshBasicMaterial({ toneMapped: false })
  const nodeMesh = new THREE.InstancedMesh(
    nodeGeometry,
    nodeMaterial,
    Math.max(1, layout.clusters.length),
  )
  nodeMesh.frustumCulled = false

  const satelliteCount = layout.clusters.reduce(
    (sum, cluster) => sum + cluster.satellites.length,
    0,
  )
  const satelliteGeometry = new THREE.OctahedronGeometry(1, 0)
  const satelliteMaterial = new THREE.MeshBasicMaterial({ toneMapped: false })
  const satelliteMesh = new THREE.InstancedMesh(
    satelliteGeometry,
    satelliteMaterial,
    Math.max(1, satelliteCount),
  )
  satelliteMesh.frustumCulled = false

  const matrix = new THREE.Matrix4()
  const quaternion = new THREE.Quaternion()
  const scaleVector = new THREE.Vector3()
  const color = new THREE.Color()
  const glowPositions: number[] = []
  const tickPositions: number[] = []
  let satelliteIndex = 0

  layout.clusters.forEach((cluster, index) => {
    const lit = cluster.state === 'lit'
    const x = cluster.x * SCALE
    const z = cluster.y * SCALE
    const y = Math.sin(cluster.angle * 3.1) * 0.14
    const size = lit ? 0.08 + cluster.brightness * 0.07 : 0.055
    const nodeColor = lit ? 0xffb478 : 0x4f627d

    matrix.compose(
      new THREE.Vector3(x, y, z),
      quaternion.setFromAxisAngle(
        new THREE.Vector3(0.3, 1, 0.2).normalize(),
        cluster.angle,
      ),
      scaleVector.setScalar(size),
    )
    nodeMesh.setMatrixAt(index, matrix)
    nodeMesh.setColorAt(index, color.setHex(nodeColor))

    if (lit) {
      glowPositions.push(x, y, z)
      tickPositions.push(x, y, z, x * 1.06, y, z * 1.06)
    }

    for (const satellite of cluster.satellites) {
      const satelliteX = x + satellite.dx * SCALE
      const satelliteZ = z + satellite.dy * SCALE
      const satelliteY = y + Math.sin(satellite.phase) * 0.05
      const satelliteSize = lit ? 0.018 + cluster.brightness * 0.022 : 0.012
      matrix.compose(
        new THREE.Vector3(satelliteX, satelliteY, satelliteZ),
        quaternion.identity(),
        scaleVector.setScalar(satelliteSize),
      )
      satelliteMesh.setMatrixAt(satelliteIndex, matrix)
      satelliteMesh.setColorAt(satelliteIndex, color.setHex(nodeColor))
      satelliteIndex += 1
    }
  })

  nodeMesh.instanceMatrix.needsUpdate = true
  if (nodeMesh.instanceColor) nodeMesh.instanceColor.needsUpdate = true
  satelliteMesh.instanceMatrix.needsUpdate = true
  if (satelliteMesh.instanceColor) satelliteMesh.instanceColor.needsUpdate = true
  root.add(nodeMesh, satelliteMesh)

  if (tickPositions.length) {
    const geometry = new THREE.BufferGeometry()
    geometry.setAttribute(
      'position',
      new THREE.Float32BufferAttribute(tickPositions, 3),
    )
    const material = new THREE.LineBasicMaterial({
      color: 0x5c708c,
      transparent: true,
      opacity: 0.25,
    })
    root.add(new THREE.LineSegments(geometry, material))
  }

  if (glowPositions.length && glowTexture) {
    const geometry = new THREE.BufferGeometry()
    geometry.setAttribute(
      'position',
      new THREE.Float32BufferAttribute(glowPositions, 3),
    )
    const material = new THREE.PointsMaterial({
      size: 0.55,
      map: glowTexture,
      color: 0xffb478,
      transparent: true,
      opacity: 0.65,
      depthWrite: false,
      blending: THREE.AdditiveBlending,
      sizeAttenuation: true,
    })
    root.add(new THREE.Points(geometry, material))
  }

  if (layout.residual.length && starTexture) {
    const count = layout.residual.length
    const positions = new Float32Array(count * 3)
    const colors = new Float32Array(count * 3)
    layout.residual.forEach((node, index) => {
      positions[index * 3] = node.x * SCALE
      positions[index * 3 + 1] = Math.sin(node.phase) * 0.2
      positions[index * 3 + 2] = node.y * SCALE
      const tone = new THREE.Color(node.tone === 'warm' ? 0xffc48a : 0x9fb8d8)
      colors[index * 3] = tone.r
      colors[index * 3 + 1] = tone.g
      colors[index * 3 + 2] = tone.b
    })
    const geometry = new THREE.BufferGeometry()
    geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3))
    geometry.setAttribute('color', new THREE.BufferAttribute(colors, 3))
    const material = new THREE.PointsMaterial({
      size: 0.2,
      map: glowTexture ?? starTexture,
      vertexColors: true,
      transparent: true,
      opacity: 0.9,
      depthWrite: false,
      blending: THREE.AdditiveBlending,
      sizeAttenuation: true,
    })
    root.add(new THREE.Points(geometry, material))
  }
}

function updateProgress(progress: number): void {
  if (!scene) return
  if (progressMesh) {
    scene.remove(progressMesh)
    progressMesh.geometry.dispose()
    const material = progressMesh.material
    if (Array.isArray(material)) material.forEach((item) => item.dispose())
    else material.dispose()
    progressMesh = null
  }
  if (progress <= 0) return

  const geometry = new THREE.RingGeometry(0.82, 0.95, 96, 1, 0, progress * TAU)
  const material = new THREE.MeshBasicMaterial({
    color: 0xff7a3c,
    transparent: true,
    opacity: 0.8,
    side: THREE.DoubleSide,
    toneMapped: false,
  })
  const mesh = new THREE.Mesh(geometry, material)
  mesh.rotation.x = -Math.PI / 2
  mesh.position.y = 0.02
  scene.add(mesh)
  progressMesh = mesh
}

function renderFrame(): void {
  if (renderer && scene && camera) renderer.render(scene, camera)
}

function animate(now: number): void {
  frame = requestAnimationFrame(animate)
  const delta = Math.min(0.05, (now - lastTime) / 1000)
  lastTime = now
  if (root && !reduced) root.rotation.y += delta * 0.045
  controls?.update()
  if (renderer && scene && camera) renderer.render(scene, camera)
}

function start(): void {
  if (frame) return
  lastTime = performance.now()
  frame = requestAnimationFrame(animate)
}

function stop(): void {
  if (frame) {
    cancelAnimationFrame(frame)
    frame = 0
  }
}

function handleVisibility(): void {
  if (document.hidden) stop()
  else if (props.active) start()
}

function handleKey(event: KeyboardEvent): void {
  if (!camera || !controls) return
  const step = 0.12
  const offset = camera.position.clone().sub(controls.target)
  const spherical = new THREE.Spherical().setFromVector3(offset)
  if (event.key === 'ArrowLeft') spherical.theta -= step
  else if (event.key === 'ArrowRight') spherical.theta += step
  else if (event.key === 'ArrowUp') spherical.phi = Math.max(0.3, spherical.phi - step)
  else if (event.key === 'ArrowDown') {
    spherical.phi = Math.min(Math.PI - 0.35, spherical.phi + step)
  } else return
  event.preventDefault()
  offset.setFromSpherical(spherical)
  camera.position.copy(controls.target).add(offset)
  controls.update()
}

function init(): void {
  const element = host.value
  if (!element) return

  try {
    renderer = new THREE.WebGLRenderer({
      antialias: true,
      alpha: true,
      powerPreference: 'high-performance',
    })
  } catch {
    failed.value = true
    return
  }

  renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2))
  renderer.setSize(element.clientWidth, element.clientHeight, false)
  renderer.domElement.style.width = '100%'
  renderer.domElement.style.height = '100%'
  renderer.domElement.style.display = 'block'
  renderer.domElement.style.touchAction = 'none'
  renderer.domElement.style.cursor = 'grab'
  renderer.domElement.setAttribute('data-testid', 'galaxy-canvas-3d')
  element.appendChild(renderer.domElement)

  scene = new THREE.Scene()
  scene.background = new THREE.Color(0x06070b)
  scene.fog = new THREE.FogExp2(0x06070b, 0.035)

  camera = new THREE.PerspectiveCamera(
    42,
    element.clientWidth / Math.max(1, element.clientHeight),
    0.1,
    120,
  )
  camera.position.set(6.8, 4.4, 9)
  camera.lookAt(0, 0, 0)

  controls = new OrbitControls(camera, renderer.domElement)
  controls.enableDamping = true
  controls.dampingFactor = 0.07
  controls.enablePan = false
  controls.minDistance = 4.2
  controls.maxDistance = 18
  controls.minPolarAngle = 0.25
  controls.maxPolarAngle = Math.PI - 0.3
  controls.rotateSpeed = 0.75
  controls.zoomSpeed = 0.7
  controls.target.set(0, 0, 0)
  controls.addEventListener('start', () => {
    if (renderer) renderer.domElement.style.cursor = 'grabbing'
  })
  controls.addEventListener('end', () => {
    if (renderer) renderer.domElement.style.cursor = 'grab'
  })

  root = new THREE.Group()
  scene.add(root)

  starTexture = makeRadialTexture([
    [0, 'rgba(255, 255, 255, 1)'],
    [0.35, 'rgba(255, 255, 255, 0.65)'],
    [1, 'rgba(255, 255, 255, 0)'],
  ])
  glowTexture = makeRadialTexture(
    [
      [0, 'rgba(255, 220, 180, 0.95)'],
      [0.25, 'rgba(255, 160, 90, 0.5)'],
      [1, 'rgba(255, 120, 60, 0)'],
    ],
    128,
  )

  reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches
  buildStarfield()
  buildCore()
  buildSceneContent()
  updateProgress(props.progress)
  resize()

  if (props.active) start()
  else renderFrame()
  document.addEventListener('visibilitychange', handleVisibility)

  observer = new ResizeObserver(() => resize())
  observer.observe(element)
}

onMounted(init)

watch(
  () => props.skills,
  () => {
    buildSceneContent()
    if (!props.active) renderFrame()
  },
)

watch(
  () => props.progress,
  (value) => {
    updateProgress(value)
    if (!props.active) renderFrame()
  },
)

watch(
  () => props.active,
  (active) => {
    if (active) {
      resize()
      start()
    } else {
      stop()
    }
  },
)

onBeforeUnmount(() => {
  stop()
  observer?.disconnect()
  document.removeEventListener('visibilitychange', handleVisibility)
  controls?.dispose()
  if (scene) disposeObject(scene)
  starTexture?.dispose()
  glowTexture?.dispose()
  renderer?.dispose()
  if (renderer?.domElement.parentElement) {
    renderer.domElement.parentElement.removeChild(renderer.domElement)
  }
  renderer = null
  scene = null
  camera = null
  controls = null
  root = null
})
</script>

<template>
  <GalaxyCanvas
    v-if="failed"
    :skills="skills"
    :progress="progress"
    :active="active"
  />
  <div
    v-else
    ref="host"
    class="galaxy-scene"
    data-testid="galaxy-scene"
    tabindex="0"
    role="application"
    aria-label="三维记忆星系，可拖动旋转，滚轮缩放，方向键旋转"
    @keydown="handleKey"
  />
</template>

<style scoped>
.galaxy-scene {
  width: 100%;
  height: 100%;
  outline: none;
  cursor: grab;
}

.galaxy-scene:active {
  cursor: grabbing;
}

.galaxy-scene:focus-visible {
  outline: 2px solid var(--accent);
  outline-offset: -2px;
}
</style>
