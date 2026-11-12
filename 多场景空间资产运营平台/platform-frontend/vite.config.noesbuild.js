import base from './vite.config.js'
export default { ...base, esbuild: false, build: { ...(base.build || {}), minify: false } }
