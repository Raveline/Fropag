/** Chart builders **/
function init_fropag(packages, then) {
    google.load('visualization', '1.0', {'packages':packages});
    google.setOnLoadCallback(then);
    // Prepare the navbar form
    $('#search-word').submit(function(e) {
        var word = $('input[name="wordsearch"]').val();
        if (word.length > 0) {
            window.location.href="/word/" + word;
        }
        e.preventDefault();
    });
}

function one_ajax_for_nodes(data, url, nodes, draw_func, values) {
    values = values 
    $.get(url, data, function(data) {
        nodes.each(function(index, node) {
            relevant_data = data;
            if (values) {
              name = values[index];
              if (name in data) {
                  relevant_data = data[name];
              }
            }
            draw_func(node, name, relevant_data);
        });
    });
}

function title_text_extractor(node) {
    return $(node).children('h3').text();
}

function one_publish(url, selected_class, chart_func, data) {
  data = data || {};
  one_ajax_for_nodes(data, url, $(selected_class), chart_func);
}

function box_publish(url) {
    /** For each followed publications,
    display a little chart. **/
    selected = $('.pub-box');
    var values = [];
    selected.each(function(index, node) {
        values.push(title_text_extractor(node));
    });
    var args = { 'names[]' : values };
    one_ajax_for_nodes(args, url, selected, draw_double_col_chart, values);
}

function draw_double_col_chart(dom_node, name, stats) {
    /** Will draw two bar_charts : one for the proper nouns,
    the other for the common ones.**/
    var box_node = $(dom_node);
    var propers = box_node.children('.proper').get(0);
    var commons = box_node.children('.commons').get(0);
    add_time_scale(box_node, name, stats['mindate'], stats['maxdate']);
    draw_col_chart(propers, name, stats['propers']);
    draw_col_chart(commons, name, stats['commons']);
}

function add_time_scale(dom_node, name, min, max) {
    text = ['<div class="legend">', 'Entre le ', min, ' et ', max, '</div>'].join('');
    dom_node.append(text);
}

function draw_col_chart(dom_node, name, stats) {
    /** Stats should be in the form :
    [['Word', 'Usage'],
    ['Hello', 1]...]**/
    var data = google.visualization.arrayToDataTable(stats);
    var options = { title : "Mots les plus fréquents sur la page d'accueil" };
    var chart = new google.visualization.ColumnChart(dom_node);
    chart.draw(data,options);
}

function draw_histo_chart(dom_node, name, stats) {
    var data = google.visualization.arrayToDataTable(stats.data);
    var options = { title : "Historique d'utilisation du mot"
                    , curveType: "function" };
    var chart = new google.visualization.LineChart(dom_node);
    chart.draw(data,options);
}

function draw_double_bars(dom_node, name, stats) {
    var box_node = $(dom_node);
    var propers = box_node.children('.propers').get(0);
    var commons = box_node.children('.commons').get(0);
    add_time_scale(box_node, name, stats['mindate'], stats['maxdate']);
    draw_words_bar(propers, name, stats['propers']);
    draw_words_bar(commons, name, stats['commons']);
}

function draw_words_bar(dom_node, name, stats) {
    var data = google.visualization.arrayToDataTable(stats);
    var options = { title : "Mots les plus fréquents sur la page d'accueil" };
    var chart = new google.visualization.BarChart(dom_node);
    chart.draw(data,options);
}

function data_to_bar_chart(data, node, begin_color, end_color) {
	// Remove the legend from our data
	var legend = data.shift()
	
	// Compute size
	var margin = {top: 20, right : 30, bottom:30, left:40};
	var height = 352 - margin.top - margin.bottom;
	var width = parseInt(node.style("width")) - margin.top - margin.bottom;
	
	var bar_width = height / data.length;
	
	// Create the svg
	var svg = node.append("svg")
				  .attr("width", width + margin.left + margin.right)
				  .attr("height", height + margin.top + margin.bottom)
				.append("g")
					.attr("transform", "translate(" + margin.left + "," + margin.top + ")");

	// Prepare the scale
	var y = d3.scale.linear()
			  .domain([0, d3.max(data, function(d) { return d[1] })])
			  .range([height,0]);
	
	var x = d3.scale.ordinal()
			.domain(data.map(function(d) { return d[0]; }))
			.rangeRoundBands([0, width], 0,0);

	var color = d3.scale.linear()
				  .domain([0,100])
				  .interpolate(d3.interpolateRgb)
				  .range([begin_color, end_color]);
			
	var bar = svg.selectAll("g")
				 .data(data)
			     .enter().append("g")
				 .attr("transform", function(d) { 
					return "translate (" + x(d[0]) + ", 0)"; 
				 });

		 
	bar.append("rect")
		.attr("y", function(d) { return y(d[1]) })
		.attr("width", x.rangeBand())
		.attr("height", function(d) { return height - y(d[1]) })
		.style("fill", function(d) { return color(d[1]); });
	
	// Add the axis
	var xAxis = d3.svg.axis().scale(x).orient("bottom");
	svg.append("g")
		.attr("class", "x axis")
		.attr("transform", "translate(0," + height + ")")
		.call(xAxis);
	var yAxis = d3.svg.axis().scale(y).orient("left");
	svg.append("g")
		.attr("class", "y axis")
		.attr("transform", "translate(0,0)")
		.call(yAxis);

}
