const React = require('react')

// Web shim: provide simple mock components to avoid importing native modules on web
const MockMap = (props) => React.createElement('div', { style: { width: '100%', height: '100%', ...props.style } }, props.children)
const MockMarker = (props) => React.createElement('div', { style: { display: 'none' } }, props.title || 'Marker')

module.exports = { default: MockMap, MapView: MockMap, Marker: MockMarker }
