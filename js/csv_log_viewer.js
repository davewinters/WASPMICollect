<!-- declare variables -->
var filename  = '';
var lines = [];
var dates = [];
var _ykeys = [];
var _ykeys_div = [];
var colors = [];
var colors_html = '';
var regex_date   = new RegExp( "(\\d+)(\\d+)/(\\d+)(\\d+)/(\\d+)(\\d+)(\\d+)(\\d+)", "i");

function purge_data () {
       lines = [];
       dates = [];
       _ykeys = [];
       colors = [];
       colors_html = '';
}

function getRandomColor() {
  var letters = '0123456789ABCDEF'.split('');
  var color = '#';
  for (var i=0; i<6; i++) {
    color += letters[ Math.floor( Math.random()*16)];
  }
  return color;
}

function getRainbowColor( numOfSteps, step) {
  var r,g,b;
  var h = step / numOfSteps;
  var i = ~~(h*6);
  var f = h*6 - i;
  var q = 1 - f;
  switch (i%6) {
    case 0: r=1, g=f, b=0; break;
    case 1: r=q, g=1, b=0; break;
    case 2: r=0, g=1, b=f; break;
    case 3: r=0, g=q, b=1; break;
    case 4: r=f, g=0, b=1; break;
    case 5: r=1, g=0, b=q; break;
  }
  var c = "#" + ("00" + (~ ~(r*255)).toString(16)).slice(-2) + ("00" + (~ ~(g*255)).toString(16)).slice(-2) + ("00" + (~ ~(b*255)).toString(16)).slice(-2)
  return c;
}

function generateColors( data) {
  var l = data.length;
  console.log( l);
  for (d in data) {
    // colors.push( getRainbowColor( l, d));
    colors.push( getRandomColor());
  }
  for (c in colors) {
    colors_html += ' <span style="color:' + colors[ c] + '">' + colors[ c] + '</span>'
  }
}

<!-- updateGraph -->
function updateGraph() {
        var current_date = $('#date_picker').val();
        console.log("updateGraph() called for date: " + current_date);
        console.log("lines: " + lines);
        var _data = [];
        for (line in lines) {
                var l = lines[ line].split(';');
                // console.log( l);
                var _t = {};
                for (i in l) {
                        if ( l[i] != '') {
                                if (i == 0) { _t[ 't'] = l[ i]; }
                                else {
                                  _t[ _ykeys[ i - 1]] = (l[ i] / _ykeys_div[ i - 1]).toFixed(0);
                                  // console.log( i + ':' + _ykeys[ i - 1] + ':' + l[ i]);
                                }
                        }
                }
                // console.log( _t);
                if (current_date == lines[ line].split(" ")[0]) {
                        _data.push( _t);
                }
        }
        // console.log( _data);

        console.log( "_data:");
        console.log( _data);

        $('#graph').empty();
        Morris.Line({
                element: 'graph',
                data: _data,
                xkey: 't',
                ykeys: _ykeys,
                labels: _ykeys,
                lineColors: colors,
                parseTime: false,
                hoverCallback: function (index, options, content) {
                  var date_time = options.data[ index].t.split(' ');
                  var text = "<table>\n"
                  text = text + " <thead> <th> </th> <th class='label'> " + date_time[0] + " </th> <th class='val'> " + date_time[1] + " </th> </thead>\n";
                  for (y in _ykeys) {
                    value = options.data[index][ _ykeys[y]];
                    text = text + "<tr> <td style='font-weight:bold; color:" + colors[y]+ ";'> (color) &nbsp;&nbsp; </td> <td class='label'> " + _ykeys[y] + " </td> <td class='val'> " + value + " </td> </tr>\n";
                  }
                  text = text + "</table>\n"
                  $("#msg").empty();
                  $("#msg").append( text);
                  // return text;
                  // do not display over
                  return '';
                }
        }).on('click', function(i, row){
          // console.log(i, row);
        });
}

function parse_data (data) {
	console.log( 'parsing data for filename: ' + filename);
        $('#filename').text( filename);

        purge_data();
        $('#date_picker').empty();

        console.log( typeof( data));
        console.log( '--- data ---');
        // console.log( data);
        console.log( '------------');

        // $('#log').click( function() { $('#log_content').slideToggle();});
        // $('#log_content').hide();

        var datas = data.split('\n');
        console.log( '--- datas ---');
        // console.log( datas);
        console.log( '-------------');
        for (l in datas) {
          if (l == 0) {
            _ykeys = datas[ l].split(';').slice(1);
            for (y in _ykeys) {
              var _ykeys_split =  _ykeys[ y].split(':')
              if ( _ykeys_split.length >= 2) {
                _ykeys[ y] = _ykeys_split[0];
                _ykeys_div[ y] = _ykeys_split[1];
              } else {
                _ykeys_div[ y] = 1;
              }
            }
          }
          else {
            data_date = regex_date.exec( datas[ l]);
            if (data_date) {
                console.log( l + ':' + datas[l]);
                var ll = datas[ l].replace( new RegExp("/","gm"), '-');
                // $('#log_content').append('</br>' + ll);
                lines.push( ll);
                var d = ll.split(" ")[0];
                // console.log( 'd:' + d);
                if ($.inArray( d, dates) < 0 && (d != "")) {
                  dates.push( d);
                  // console.log( 'dates:' + dates);
                  $('#date_picker').append( $('<option>', { value: d, text: d}));
                }
            }
          }
        }
        
        if ( $('#date_picker > option').length == 0) { $('#date_picker').hide(); }
        else { $('#date_picker').show(); }
        $('#date_picker option:last').attr("selected","selected");
        var dl = $('#date_picker option').length
        if (dl == 0 || dl == 1) { $('.button').hide();}
        else { $('.button').show();}
        // $('#prev, #next').click( function() { $('#date_picker :selected')[this.id]().prop('selected',true); updateGraph();});
	console.log('_ykeys:' + _ykeys);
	console.log('_ykeys_div:' + _ykeys_div);

        generateColors( _ykeys);
        updateGraph();
}

function handleLogFileSelect( evt) {
       var l = $('#logfile :selected').val();
       console.log( 'logfile selected: ' + l);
       filename = $('#logfile :selected').text();

       // clear file input
       $('#files').val('');   
       $('#files').replaceWith( $('#files').clone( true));
       document.getElementById('files').addEventListener('change', handleFileSelect, false);

       $.get( l, parse_data);
}

function handleFileSelect( evt) {
        var all_lines = [];
        // document.getElementById('container').innerHTML = "";
        var files = evt.target.files; // FileList object
        console.log( 'files.length:' + files.length);
        for (var i=0, f; f=files[i]; i++) {
                filename = f.name;
                var reader = new FileReader();
                reader.onload = function( event) {
                        // event.target point to FileHandler
                        var contents = event.target.result;
                        var lines = contents.split('\n');
                        console.log( "lines length:" + lines.length);
                        all_lines = all_lines.concat( [], lines);
                        // console.log( "all_lines length:" + all_lines.length);
                        // console.log( all_lines.join( ";"));
                        // document.getElementById('container').innerHTML = all_lines.join( "<br/>");
                        if (i == files.length) { parse_data( all_lines.join( '\n'));}
                };
                reader.readAsText(f);
        }
        // console.log( all_lines.length);
  }

<!-- Retrieve and Display log content -->
function documentReady( logfile) {
  // purge_data();
  $(document).ready( $.get( logfile, parse_data));
  document.getElementById('logfiles').addEventListener('change', handleLogFileSelect, false);
  document.getElementById('files').addEventListener('change', handleFileSelect, false);
  document.getElementById('date_picker').addEventListener('change', updateGraph, false);
  $('#prev').click( function() { $('#date_picker').val( $('#date_picker :selected').prev().val()); updateGraph()});
  $('#next').click( function() { $('#date_picker').val( $('#date_picker :selected').next().val()); updateGraph()});
  if ( $('#logfile > option').length == 0) { $('#logfiles').hide(); }
}

