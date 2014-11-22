var d3rainbow = ['red', 'yellow', 'blue', 'violet', 'orange', 'green', 'indigo'].map(function(s) { return d3.rgb(s); });

/** Types **/
ColorWheel = function(wheel) {
    this.wheel = wheel;
    this.cursor = 0;
};
ColorWheel.prototype.next = function() { 
    this.cursor++;
    return this.wheel[(this.cursor - 1) % this.wheel.length];
};
ColorWheelless = function(color) {
    this.wheel = [color];
    this.cursor = 0;
}
ColorWheelless.prototype = new ColorWheel();
ColorWheelless.prototype.constructor = ColorWheelless;

/** Initialization. We'll most likely need to change that. **/
function init_fropag(then) {
    // Prepare the navbar form
    $('#search-word').submit(function(e) {
        var word = $('input[name="wordsearch"]').val();
        if (word.length > 0) {
            window.location.href="/word/" + word;
        }
        e.preventDefault();
    });
    then();
}

/** Given an object, recursively get every numeric data type it contains.**/
function extract_numbers(data) {
    var res = [];
    for (i in data) {
        type = typeof(data[i]);
        if (type == 'number') {
            res.push(data[i]);
        } else if (type == 'object') {
            res = res.concat(extract_numbers(data[i]));
        }
    }
    return res;
}

/** Given an object, extract its numeric data and return the min and max
 * of the ensemble. This let us know the global scale of displayed data.**/
function min_max(data) {
    numbers = extract_numbers(data);
    return { 'min' : d3.min(numbers), 'max' : d3.max(numbers) };
}

function one_ajax_for_nodes(data, url, nodes, colors, draw_func, values) {
    $.get(url, data, function(answer) {
        scale = min_max(answer);
        nodes.each(function(index, node) {
            // 1. Make sure this is a success
            if ("success" in answer) {
                relevant_data = answer.data;
                // 2. Multi-publication case
                if (values) {
                    name = values[index];
                    if (name in answer.data) {
                        relevant_data = answer.data[name];
                    }
                }
            }
            draw_func(relevant_data, node, colors.next(), scale);
        });
    });
}

function title_text_extractor(node) {
    return $(node).children('h3').text();
}

function one_publish(url, selected_class, color, chart_func, data) {
  data = data || {};
  one_ajax_for_nodes(data, url, $(selected_class), color, chart_func);
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
    one_ajax_for_nodes(args,
                       url, 
                       selected, 
                       new ColorWheel(d3rainbow),
                       draw_double(data_to_col_chart),
                       values);
}

function add_time_scale(dom_node, name, min, max) {
    text = ['<div class="legend">', 'Entre le ', min, ' et ', max, '</div>'].join('');
    dom_node.append(text);
}

function draw_double(func) {
    return function(data, node, tone, scale) {
        var box_node = $(node);
        var propers_node = box_node.children('.propers').get(0);
        var commons_node = box_node.children('.commons').get(0);
        func(data['propers'], propers_node, tone, scale);
        func(data['commons'], propers_node, tone, scale);
    }
}

function data_to_col_chart(data, node, tone, tone_scale) {
    title = data.title;
    data = data.data;
    // Get node as d3 object
    node = d3.select(node);
	// Remove the legend from our data
	var legend = data.shift()
	
	// Compute size
	var margin = {top: 30, right : 30, bottom:80, left:40};
	var height = 352 - margin.top - margin.bottom;
	var width = parseInt(node.style("width")) - margin.top - margin.bottom;
	
	// Create the svg
	var svg = node.append("svg")
				  .attr("width", width + margin.left + margin.right)
				  .attr("height", height + margin.top + margin.bottom)
				.append("g")
					.attr("transform", "translate(" + margin.left + "," + margin.top + ")");

	// Prepare the scale
	var maximum = d3.max(data, function(d) { return d[1] });
	var y = d3.scale.linear()
			  .domain([0, maximum])
			  .range([height,0]);
	
	var x = d3.scale.ordinal()
			.domain(data.map(function(d) { return d[0]; }))
			.rangeRoundBands([0, width], .1,0);

	var color = d3.scale.linear()
				  .domain([0, (tone_scale.max * 2)])
				  .interpolate(d3.interpolateRgb)
				  .range(["#FFFACD", tone]);
			
	var bar = svg.selectAll("g")
				 .data(data)
			     .enter().append("g");

	bar.append("rect")
        .attr("x", function(d) { return x(d[0]); })
		.attr("y", function(d) { return y(d[1]); })
		.attr("width", x.rangeBand())
		.attr("height", function(d) { return height - y(d[1]) })
		.style("fill", function(d) { return color(d[1]); });

    bar.append("text")
        .attr("x", function(d) { return x(d[0]) + x.rangeBand() / 2; })
        .attr("y", function(d) { return y(d[1]) + 12; })
        .attr("text-anchor", "middle")
        .attr("fill", "black")
        .attr("font-size", ".9em")
        .attr("visibility", "hidden")
        .text(function(d) { return d[1]; });
    
    bar.on("mouseover", function(d) { 
            d3.select(this).select('text').attr('visibility', 'visible'); 
        });
    bar.on("mouseout", function(d) {
            d3.select(this).select('text').attr('visibility', 'hidden');
    });

	// Add the axis
	var xAxis = d3.svg.axis().scale(x).orient("bottom");
	svg.append("g")
		.attr("class", "x axis")
		.attr("transform", "translate(0," + height + ")")
		.call(xAxis)
        .selectAll("text") // Rotation of text to make it legible
            .style("text-anchor", "end")
            .style("font-size", ".8em")
            .style("text", "sans serif")
            .attr("dx", "-.8em")
            .attr("dy", ".15em")
            .attr("transform", "rotate(-65)");
	var yAxis = d3.svg.axis().scale(y).orient("left");
	svg.append("g")
		.attr("class", "y axis")
		.attr("transform", "translate(0,0)")
		.call(yAxis);

    // Add the title
    svg.append("g")
       .append("text")
       .attr("y", 0-margin.top/2)
       .attr("x", width/2)
       .attr("text-anchor", "middle")
       .style("font-size", ".8em")
       .style("fill", "black")
       .text(title);
}

function data_to_bar_chart(data, node, tone, tone_scale) {
    title = data.title;
    data = data.data;
    // Node as d3 object
    node = d3.select(node);
    // Remove the legend from our data
    var legend = data.shift();
    // Compute size
    var margin = {top: 80, right : 30, bottom:30, left:40};
    var bar_height = 20;
    var height = bar_height * (data.length)
    var width = parseInt(node.style("width")) - margin.top - margin.bottom;
    var bar_width = height / data.length;
    
    // Create the svg
    var svg = node.append("svg")
                  .attr("width", width + margin.left + margin.right)
                  .attr("height", height + margin.top + margin.bottom)
                  .append("g")
                  .attr("transform", "translate(" + margin.left + "," + margin.top + ")");
    
    var color = d3.scale.linear()
                        .domain([0,(tone_scale.max)])
                        .interpolate(d3.interpolateRgb)
                        .range(["#FFFACD", tone]);
    
    // Prepare the scale
    var x = d3.scale.linear()
              .domain([0, d3.max(data, function(d) { return d[1]; })])
              .range([0, width]);
    
    var bar = svg.selectAll("g")
                 .data(data)
                 .enter().append("g")
                    .attr("transform", function(d,i) { 
                        return "translate (0," + i * bar_height + ")"; 
                    })
   
    bar.append("rect")
        .attr("x", 0)
        .attr("width", function(d) { return x(d[1]); })
        .attr("height", bar_height - 1)
        .style("fill", function(d) { return color(d[1]); });

    bar.append("text")
       .attr("x", 3)
       .attr("y", bar_height/2 + 4)
       .style("font-size", ".8em")
       .style("fill", "black")
       .text(function(d) { return [d[0], " (", d[1], ")"].join(''); });
    
    // Add the axis
    var xAxis = d3.svg.axis().scale(x).orient("top");
    svg.append("g")
    .attr("class", "x axis")
    .attr("transform", "translate(0,0)")
    .call(xAxis);

    // Add the title
    svg.append("g")
       .append("text")
       .attr("y", 0-margin.top/2)
       .attr("x", width/2)
       .attr("text-anchor", "middle")
       .style("font-zie", "1em")
       .style("fill", "black")
       .text(title);
}


function data_to_line_chart(data, node, tone, tone_scale) {
  // Node as d3 object
  node = d3.select(node);
  // Separate title and data
  var title = data.title;
  data = data.data;

  // We'll need this as a list of objects
  var as_csv = d3.csv.formatRows(data);
  var parsed = d3.csv.parse(as_csv);

  // With date properly parsed
  var parseDate = d3.time.format("%Y/%m/%d").parse;
  parsed.forEach(function(d) { d.date = parseDate(d.date); });

  // Compute size
  var margin = {top: 20, right : 80, bottom:30, left:40};
  var bar_height = 20;
  var height = 300;
  var width = parseInt(node.style("width")) - margin.top - margin.bottom;

  // Add the svg
  var svg = node.append("svg")
                .attr("width", width + margin.left + margin.right)
                .attr("height", height + margin.top + margin.bottom)
                .append("g")
                .attr("transform", "translate(" + margin.left + "," + margin.top + ")");

  // Add colors
  var color = d3.scale.category10();
  color.domain(d3.keys(parsed[0]).slice(1));

  // Objects properly defined
  var publications = color.domain().map(function(name) {
      return {
        name : name,
        values : parsed.map (function(d) {
          return {date : d.date, count: +d[name]};
        })
      }
  });

  // Prepare scales
  var x = d3.time.scale()
            .domain(d3.extent(parsed, function(d) { return d.date }))
            .range([0, width]);

  var y = d3.scale.linear()
            .domain([d3.min(publications, function(d) { return d3.min(d.values, function(v) { return v.count; }); }),
                     d3.max(publications, function(d) { return d3.max(d.values, function(v) { return v.count; }); })])
            .range([height, 0]);

  var xAxis = d3.svg.axis()
                .scale(x)
                .tickFormat(d3.time.format('%d/%m/%Y'))
                .orient("bottom");

  var yAxis = d3.svg.axis()
                .scale(y)
                .orient("left");

  // Draw lines
  var line = d3.svg.line()
               .interpolate("basis")
               .x(function(d) { return x(d.date); })
               .y(function(d) { return y(d.count); });

  svg.append("g")
     .attr("class", "x axis")
     .attr("transform", "translate (0, " + height + ")")
     .call(xAxis);

  svg.append("g")
     .attr("class", "y axis")
     .call(yAxis);

  var publication = svg.selectAll(".publications")
                       .data(publications)
                       .enter().append("g")
                       .attr("class", "publications");

  var tooltip = d3.select("body")
                  .append("div")
                  .style("position", "absolute")
                  .style("z-index", "10")
                  .style("visibility", "hidden")
                  .text("");

  publication.append("path")
             .attr("class", "line")
             .attr("id", function(d) { return "path" + normalized_string(d.name); })
             .attr("d", function(d) { return line(d.values); })
             .style("fill", "none")
             .style("stroke", function(d) { return color(d.name); })
             .style("stroke-width", 2)
             .on("mouseover", function(d, i, c) { var mouse = d3.mouse(this);
                                                  var xv = x.invert(mouse[0]);
                                                  var yv = y.invert(mouse[1]).toFixed(2);
                                                  return tooltip.style("visibility", "visible")
                                                                .text(xv.toLocaleDateString() + " : " + yv);})
             .on("mousemove", function() { return tooltip.style("top", (event.pageY-10)+"px")
             .style("left",(event.pageX+10)+"px"); })
             .on("mouseout", function() { return tooltip.style("visibility", "hidden") });

  publication.append("text")
             .attr("x", width)
             .attr("y", function(d,i) { return i * 20 })
             .attr("text-anchor", "right")
             .attr("cursor", "pointer")
             .attr("fill", function(d) { return color(d.name); })
             .text(function(d) { return d.name; })
             .on("click", function(d, i, c) { var line = "#path" + normalized_string(d3.select(this).text());
                                              var path = d3.select(line);
                                              if (path.attr('visibility') == 'hidden') {
                                                path.attr('visibility', 'visible');
                                              } else {
                                                d3.select(line).attr('visibility', 'hidden');
                                              }
                                            });
}

function normalized_string(string) {
    return string.replace(/\s/g, '').replace(/\'/g, '');
}
