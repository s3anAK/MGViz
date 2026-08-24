// Earthquakes tool — coseismic events and green displacement vectors.

import $ from 'jquery'
import * as d3 from 'd3'

import L_ from '../../../../src/essence/Basics/Layers_/Layers_'
import ToolController_ from '../../../../src/essence/Basics/ToolController_/ToolController_'
import Map_ from '../../../../src/essence/Basics/Map_/Map_'

var VECTORS_FIL = 'clean'
var VECTORS_TYPE = 'detrend'

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
      '<span style="font-size:10px">Coseismic events and green<br>',
      'displacement arrows on the map.</span><br>',
      '<br>Coseismic Events:<br>',
      '<select id="selectEarthquakeEvent" style="color:black; width:160px">',
      '</select><br>',
      '<br>Vector source:<br>',
      '<select id="selectEarthquakeSource" style="color:black">',
      '<option value="comb">Combination</option>',
      '<option value="jpl">JPL</option>',
      '<option value="sopac">SOPAC</option>',
      '</select><br>',
      '<span style="font-size:10px">Independent of Chart Source/<br>',
      'Filter/Type. Vectors always use<br>',
      'Clean Detrend offsets.</span><br>',
      '<br>Display:<br>',
      '<select id="selectEarthquakeDisplay" style="color:black">',
      '<option value="all">All</option>',
      '<option value="greater">&gt;=20</option>',
      '</select><br>',
      '<span style="font-size:10px">Show only displacements (mm)<br>',
      'greater than selected value<br>',
      'in any horizontal direction.</span><br>',
      '<br>Exaggeration:<br>',
      '<select id="selectEarthquakeLength" style="color:black">',
      '<option value="1">1</option>',
      '<option value="2">2</option>',
      '<option value="3">3</option>',
      '</select><br>',
      '<span style="font-size:10px">Exaggerate the size<br>',
      'of arrows.</span><br>',
      '<br>',
      '<button id="buttonEarthquakeClear" style="color:black; width:160px; padding:3px;">Clear</button><br>',
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

    $('#selectEarthquakeSource').val(this.source)
    $('#selectEarthquakeDisplay').val(this.displacementFilter)
    $('#selectEarthquakeLength').val(this.displacementExaggeration)

    Map_.displacementExaggeration = this.displacementExaggeration
    Map_.displacementFilter = this.displacementFilter

    loadCoseismicEvents(this.selectedEventId)

    $('#selectEarthquakeEvent').on('change', function () {
      var id = this.value
      if (!id) return
      EarthquakesTool.loadEvent(id)
    })

    $('#selectEarthquakeSource').on('change', function () {
      EarthquakesTool.source = this.value
      if (EarthquakesTool.selectedEventId) {
        refreshVectorsLayer(EarthquakesTool.selectedEventId, EarthquakesTool.source)
      }
    })

    $('#selectEarthquakeDisplay').on('change', function () {
      EarthquakesTool.displacementFilter = this.value
      Map_.displacementFilter = this.value
      refreshVectorsStyleOnly()
    })

    $('#selectEarthquakeLength').on('change', function () {
      EarthquakesTool.displacementExaggeration = this.value
      Map_.displacementExaggeration = this.value
      refreshVectorsStyleOnly()
    })

    $('#buttonEarthquakeClear').on('click', function () {
      EarthquakesTool.clear()
    })
  },

  /** Load coseismic sites + Vectors for an event id; stay on Earthquakes (no Chart open). */
  loadEvent: function (id) {
    if (!id) return
    this.selectedEventId = id
    $('#selectEarthquakeEvent').val(id)

    $.ajax({
      type: 'GET',
      url: 'api/mgviz/coseismic?id=' + id,
      dataType: 'json',
      success: function (data) {
        var sites = []
        $.each(data['sites'], function (key, value) {
          sites.push(value.site_id)
        })
        if (sites.length === 0) {
          alert('No sites were found with the coseismic event.')
          return
        }

        stashChartSelection(sites)
        L_.resetLayerFills()
        ToolController_.getTool('SearchTool').search(sites, 'Sites', {
          skipOpenChart: true,
        })

        ensureVectorsLayerOn()
        refreshVectorsLayer(id, EarthquakesTool.source)
      },
      error: function () {
        console.error('Unable to retrieve list of coseismic sites.')
      },
    })
  },

  clear: function () {
    this.selectedEventId = null
    $('#selectEarthquakeEvent').val('')

    stashChartSelection([])
    L_.resetLayerFills()

    var vname = vectorsLayerName()
    if (vname) {
      var vectorsUrl = L_.layers.data[vname].url.substring(
        0,
        L_.layers.data[vname].url.lastIndexOf('earthquake_vectors')
      )
      L_.layers.data[vname].url = vectorsUrl + 'earthquake_vectors/0/0/0/0'
      Map_.refreshLayer(L_.layers.data[vname])
    }
  },

  destroy: function () {
    this.MMGISInterface.separateFromMMGIS()
  },

  getUrlString: function () {
    return ''
  },
}

function vectorsLayerName() {
  var uuids = L_.layers.nameToUUID['Vectors']
  return uuids && uuids[0]
}

function ensureVectorsLayerOn() {
  var vname = vectorsLayerName()
  if (vname && L_.layers.on[vname] == false) {
    L_.toggleLayer(L_.layers.data[vname])
  }
}

function refreshVectorsLayer(id, source) {
  var vname = vectorsLayerName()
  if (!vname) return
  var vectorsUrl = L_.layers.data[vname].url.substring(
    0,
    L_.layers.data[vname].url.lastIndexOf('earthquake_vectors')
  )
  L_.layers.data[vname].url =
    vectorsUrl +
    'earthquake_vectors/' +
    id +
    '/' +
    source +
    '/' +
    VECTORS_FIL +
    '/' +
    VECTORS_TYPE
  Map_.refreshLayer(L_.layers.data[vname])
}

function refreshVectorsStyleOnly() {
  var vname = vectorsLayerName()
  if (vname) Map_.refreshLayer(L_.layers.data[vname])
}

/** Remember sites for Chart Selected when Chart is reopened; clear live Chart state. */
function stashChartSelection(sites) {
  var ct = ToolController_.getTool('ChartTool')
  if (!ct) return
  ct.previousSites = sites.slice()
  ct.sites = []
  ct.site = ''
  ct.siteOptionsList = []
  ct.stackOn = false
  if ($('#siteSelect').length) {
    $('#siteSelect').empty()
    $.each(sites, function (key, value) {
      $('#siteSelect').append(
        $('<option></option>').attr('value', value).text(value)
      )
    })
  }
}

function loadCoseismicEvents(selectId) {
  $.ajax({
    type: 'GET',
    url: 'api/mgviz/coseismic/',
    dataType: 'json',
    success: function (data) {
      $('#selectEarthquakeEvent').empty()
      $('#selectEarthquakeEvent').append(
        $('<option></option>').attr('value', '').text('')
      )
      $.each(data['coseismics'], function (key, value) {
        if ('id' in value && 'time_utc' in value) {
          $('#selectEarthquakeEvent').append(
            $('<option></option>')
              .attr('value', value.id)
              .text(value.time_utc)
          )
        }
      })
      if (selectId) {
        $('#selectEarthquakeEvent').val(selectId)
      } else {
        $('#selectEarthquakeEvent').val('')
      }
    },
    error: function () {
      console.error('Unable to retrieve list of coseismics.')
    },
  })
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
