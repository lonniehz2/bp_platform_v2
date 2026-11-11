export const SCENE_ROUTES = { GUARANTEE: 'guarantee', ASSET: 'asset', SERVICE: 'service' }

export function currentScene() {
  const hash = String(location.hash || '').replace(/^#/, '')
  const matched = hash.match(/^\/scene\/([^/]+)/)
  if (matched) return matched[1].toUpperCase()
  const prefix = hash.split('/').filter(Boolean)[0]
  const found = Object.entries(SCENE_ROUTES).find(([, path]) => path === prefix)
  return found ? found[0] : (localStorage.getItem('platformScene') || 'GUARANTEE')
}

export function sceneRoot(scene = currentScene()) {
  return '/' + (SCENE_ROUTES[scene] || 'guarantee')
}

export function scenePath(path) {
  const root = sceneRoot()
  return String(path || '').startsWith('/guarantee') ? root + String(path).slice('/guarantee'.length) : path
}

export function sceneOfPath(path) {
  const prefix = String(path || '').replace(/^#/, '').split('/').filter(Boolean)[0]
  const found = Object.entries(SCENE_ROUTES).find(([, value]) => value === prefix)
  return found ? found[0] : (localStorage.getItem('platformScene') || 'GUARANTEE')
}
