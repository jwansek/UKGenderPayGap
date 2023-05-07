function collapseTogglePress(elem, a_elem, num_hidden) {
    if (getComputedStyle(document.getElementById(elem)).display === "none") {
        document.getElementById(elem).style.display = "block";
        document.getElementById(a_elem).innerText = `Hide ${num_hidden} filters`
    } else {
        document.getElementById(elem).style.display = "none";
        document.getElementById(a_elem).innerText =`Un-hide ${num_hidden} hidden filters`
    }
}

const PLOT_FUNC_MAPPINGS = {
    "years": draw_plot_years,
}

$(document).ready(function() {
    document.getElementById("filterform").action = window.location.pathname + "/apply_click";

    fetch("/api/charts.json").then((resp) => {
        resp.json().then((body) => {
            const CHARTS = body;

            var minicharts = document.getElementsByClassName("minichart");
            for (var i = 0; i < minicharts.length; i++) {
                var theId = minicharts.item(i).id;
                var u = new URL(window.location.origin + theId);
                var theIdSplit = u.pathname.split("/");

                CHARTS["index"].forEach(element => {
                    if (theId === "/minichart" + element.url) {
                        filters = element["filters"];
                    }
                });

                PLOT_FUNC_MAPPINGS[theIdSplit[theIdSplit.length - 1]](theId, filters);
            }

            var charts = document.getElementsByClassName("chart");
            for (var i = 0; i < charts.length; i++) {
                var theId = charts.item(i).id;
                var u = new URL(window.location.origin + theId);
                var theIdSplit = u.pathname.split("/");

                CHARTS["index"].forEach(element => {
                    if (theId === "/chart" + element.url) {
                        filters = element["filters"];
                    }
                });

                PLOT_FUNC_MAPPINGS[theIdSplit[theIdSplit.length - 1]](theId, filters);
            }
        })
    })
});

function form_api_url(containerName, filters) {
    var name = containerName.split("/")[containerName.split("/").length - 1];
    var url = new URL(window.location.origin + "/api/" + name);
    for (const [filterName, value] of Object.entries(filters)) {
        
        if (typeof value === 'object' && value !== null) {
            if ("default" in value) {
                // console.log(filterName, value["default"]);
                url.searchParams.append(filterName, value["default"]);
            }
        }       
    }
    return url.toString();
}

function draw_plot_years(containerName, filters) {
    fetch(form_api_url(containerName, filters)).then(resp => {
        resp.json().then((data) => {
            if (containerName.substring(1, 6) === "chart") {
                var yAxisTitle = true;
                var xAxisLabels = true;
                var showLegend = true;
            } else {
                var yAxisTitle = false;
                var xAxisLabels = false;
                var showLegend = false;
            }

            Highcharts.chart(containerName, {
                chart: {
                    zoomType: 'x',
                    type: 'area',
                },

                title: {
                    text: null
                },

                yAxis: {
                    title: {
                        enabled: yAxisTitle,
                        text: 'Percentage Pay Difference'
                    },
                    labels: {
                        format: '{value}%'
                    },
                    // tickPositioner: function () {
                    //     // var maxDeviation = Math.ceil(Math.max(Math.abs(this.dataMax), Math.abs(this.dataMin)));
                    //     // var halfMaxDeviation = Math.ceil(maxDeviation / 2);

                    //     // return [-maxDeviation, -halfMaxDeviation, 0, halfMaxDeviation, maxDeviation];
                    //     return Array.from({length: -Math.floor(this.dataMin) + 2}, (x, i) => i + Math.floor(this.dataMin));
                    // },
                },

                xAxis: {
                    type: 'category',
                    labels: {
                        enabled: xAxisLabels
                    },
                    title: {
                        text: "Year Groups",
                        enabled: yAxisTitle,
                    }
                },

                plotOptions: {
                    series: {
                        fillColor: {
                            linearGradient: [0, 0, 0, 300],
                            stops: [
                                [1, "rgba(0, 255, 0, 0.3)"]
                            ]
                        },
                        negativeFillColor: {
                            linearGradient: [0, 0, 0, 300],
                            stops: [
                                [1, "rgba(255, 0, 0, 0.3)"]
                            ]
                        }
                    }
                },
        
                series: [{
                    data: data,
                    lineWidth: 4,
                    showInLegend: showLegend,
                    name: "Pay Gap",
                    color: 'Green',
                    threshold: 0,
                    negativeColor: 'Red',
                }]
            })
        })
    })
}