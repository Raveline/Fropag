/** Chart builders **/
function init_fropag(packages, then) {
    google.load('visualization', '1.0', {'packages':packages});
    google.setOnLoadCallback(then);
}

function one_ajax_for_nodes(data, url, nodes, draw_func) {
    $.get(url, data, function(data) {
        nodes.each(function(index, node) {
            name = values[index];
            relevant_data = data;
            if (name in data) {
                relevant_data = data[name];
            } 
            draw_func(node, name, relevant_data);
        });
    });
}

function title_text_extractor(node) {
    return $(node).children('h3').text();
}

function one_publish(url, selected_class) {
  one_ajax_for_nodes({}, url, $(selected_class), draw_double_bar_chart);
}

function box_publish(url) {
    /** For each followed publications,
    display a little chart. **/
    selected = $('.pub-box');
    values = [];
    selected.each(function(index, node) {
        values.push(title_text_extractor(node));
    });
    args = { 'names[]' : values };
    one_ajax_for_nodes(args, url, selected, draw_double_bar_chart);
}

function draw_double_bar_chart(dom_node, name, stats) {
    /** Will draw two bar_charts : one for the proper nouns,
    the other for the common ones.**/
    box_node = $(dom_node);
    proper = box_node.children('.proper').get(0);
    commons = box_node.children('.commons').get(0);
    add_time_scale(box_node, name, stats['mindate'], stats['maxdate']);
    draw_bar_chart(proper, name, stats['propers']);
    draw_bar_chart(commons, name, stats['commons']);
}

function add_time_scale(dom_node, name, min, max) {
    text = ['<div class="legend">', 'Entre le ', min, ' et ', max, '</div>'].join('');
    dom_node.append(text);
}

function draw_bar_chart(dom_node, name, stats) {
    /** Stats should be in the form :
    [['Word', 'Usage'],
    ['Hello', 1]...]**/

    var data = google.visualization.arrayToDataTable(stats);
    var options = { title : "Mots les plus fréquents sur la page d'accueil" };
    var chart = new google.visualization.ColumnChart(dom_node);
    chart.draw(data,options);
}
