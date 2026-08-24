// Earthquakes tool — coseismic events and green displacement vectors.
// Step 1 scaffold: panel shell only; load path / controls come next.

import * as d3 from 'd3'

import Map_ from '../../../../src/essence/Basics/Map_/Map_'

var EarthquakesTool = {
  height: 0,
  width: 200,
  toolsDiv: null,
  source: 'comb',
  selectedEventId: null,
  displacementExaggeration: 1,
  displacementFilter: 'all',
  MMGISInterface: null,

  make: function () {
    this.MMGISInterface = new interfaceWithMMGIS()

    var panelHtml = [
      '<b>Earthquakes</b><br>',
      '<span style="font-size:10px">Coseismic event list, vector source,<br>',
      'display, and exaggeration will go here.</span><br>',
    ].join('\n')

    var tools = d3.select('#toolPanel')
    tools.selectAll('*').remove()
    tools.style('width', '200px')
    this.toolsDiv = tools
      .append('div')
      .attr('id', 'earthquakesDiv')
      .style('width', '200px')
      .style('position', 'relative')
      .style('float', 'left')
      .style('padding', '20px')
      .style('height', '50%')
      .html(panelHtml)

    Map_.displacementExaggeration = this.displacementExaggeration
    Map_.displacementFilter = this.displacementFilter
  },

  destroy: function () {
    this.MMGISInterface.separateFromMMGIS()
  },

  getUrlString: function () {
    return ''
  },
}

function interfaceWithMMGIS() {
  this.separateFromMMGIS = function () {
    separateFromMMGIS()
  }

  var tools = d3.select('#tools')
  tools.selectAll('*').remove()
  tools = tools
    .append('div')
    .attr('class', 'center aligned ui padded grid')
    .style('overflow', 'auto')
    .style('height', '100%')

  function separateFromMMGIS() {}
}

export default EarthquakesTool
