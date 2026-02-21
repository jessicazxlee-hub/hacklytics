const { getDefaultConfig } = require('@expo/metro-config')
const path = require('path')

const config = getDefaultConfig(__dirname)

// Map react-native-maps to our web shim when bundling for web to avoid importing native internals.
config.resolver = config.resolver || {}
config.resolver.extraNodeModules = config.resolver.extraNodeModules || {}
config.resolver.extraNodeModules['react-native-maps'] = path.resolve(__dirname, 'shims/react-native-maps.web.js')

module.exports = config
