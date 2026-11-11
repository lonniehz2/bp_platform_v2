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
