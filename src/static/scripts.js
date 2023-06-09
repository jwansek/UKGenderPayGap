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
    "sic_sec": draw_plot_sic_sections,
    "heatmap": draw_heatmap,
    "size": draw_plot_size,
    "type": draw_plot_type,
}

$(document).ready(function() {
    const filterform = document.getElementById("filterform");
    if (filterform !== null) {
        filterform.action = window.location.pathname + "/apply_click";
    }
    
    const slider = document.getElementById("yearslider");
    if (slider !== null) {
        slider.onchange = function() {
            fetch("/api/getyears").then(resp => {
                resp.json().then(years => {
                    document.getElementById("slider_val").innerHTML = "Year range: " + years[Number(this.value) - 1];
                });
            });
        }
    }

    if (window.location.pathname.split("/")[1] === "company") {
        appendEmployerDetails(window.location.pathname.split("/")[2]);
    }

    if (window.location.pathname.split("/")[2] === "company") {
        appendEmployerDetails(window.location.pathname.split("/")[3]);
    }

    fetch("/api/charts.json").then((resp) => {
        resp.json().then((body) => {
            const CHARTS = body;

            var minicharts = document.getElementsByClassName("minichart");
            for (var i = 0; i < minicharts.length; i++) {
                var theId = minicharts.item(i).id;
                var u = new URL(window.location.origin + theId);
                var theIdSplit = u.pathname.split("/");
                var filters;
                // console.log(theIdSplit);

                if (theIdSplit[3] === "company") {

                    const employer_id = theIdSplit[4];

                    CHARTS["employer"].forEach(element => {
                        if (theId === "/minichart" + element.url.replace("<employer>", employer_id)) {
                            filters = element["filters"];
                        }
                    });
                    // console.log("filters", filters);
                    PLOT_FUNC_MAPPINGS[theIdSplit[theIdSplit.length - 1]](theId, filters);
                } else {
                    CHARTS["index"].forEach(element => {
                        if (theId === "/minichart" + element.url) {
                            filters = element["filters"];
                        }
                    });
    
                    PLOT_FUNC_MAPPINGS[theIdSplit[theIdSplit.length - 1]](theId, filters);
                }
            }

            var charts = document.getElementsByClassName("chart");
            for (var i = 0; i < charts.length; i++) {
                var theId = charts.item(i).id;
                var u = new URL(window.location.origin + theId);
                var theIdSplit = u.pathname.split("/");

                CHARTS["index"].forEach(element => {
                    if (location.href.substr(location.href.indexOf(location.host)+location.host.length).startsWith(element["url"])) {
                        // console.log(location.href.substr(location.href.indexOf(location.host)+location.host.length), element["url"]);
                        filters = element["filters"];
                        // console.log(element);
                    }
                });

                PLOT_FUNC_MAPPINGS[theIdSplit[theIdSplit.length - 1]](theId, filters);
            }
        })
    })
});

function appendEmployerDetails(employer_id) {
    var aside = document.getElementById("theAside");
    var dl = document.createElement("dl");
    dl.classList.add("companyInfo")

    fetch("/api/" + employer_id + "/details").then(resp => {
        resp.json().then(data => {
            for (const [k, v] of Object.entries(data)) {
                if (v === null || v === "") {
                    continue;
                }
                if (k.endsWith(" Link")) {
                    dl.innerHTML += "<dt><a href='" + v + "'>" + k + "</a></dt>";
                } else {
                    dl.innerHTML += "<dt>" + k + "</dt><dd>" + v + "</dd>";
                }
            }
        })
    });
    
    aside.appendChild(dl);
}

function form_api_url(containerName, filters) {
    // console.log(filters);
    // console.log(containerName);
    var s = containerName.split("/");
    var name = s[s.length - 1];
    var url;
    if (s[3] === "company") {
        url = new URL(window.location.origin + "/api/company/" + s[4] + "/" + name);
    } else {
        url = new URL(window.location.origin + "/api/" + name);
    }
    // for (const [filterName, value] of Object.entries(filters)) {
        
    //     if (typeof value === 'object' && value !== null) {
    //         if ("default" in value) {
    //             // console.log(filterName, value["default"]);
    //             url.searchParams.append(filterName, value["default"]);
    //         }
    //     }       
    // }
    console.log("fetching ", url.toString());
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
                    plotLines: [{
                        value: 0,
                        width: 2,
                        color: 'black',
                        zIndex: 10
                    }]
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
                    showInLegend: false,
                    name: "Pay Gap",
                    color: 'Green',
                    threshold: 0,
                    negativeColor: 'Red',
                }]
            })
        })
    })
}

function draw_plot_sic_sections(containerName, filters) {
    fetch(form_api_url(containerName, filters)).then(resp => {
        resp.json().then(data => {
            if (containerName.substring(1, 6) === "chart") {
                var yAxisTitle = true;
                var xAxisLabels = true;
                var showLegend = true;
            } else {
                var yAxisTitle = false;
                var xAxisLabels = false;
                var showLegend = false;
            }
            
            var categories = [];
            var pays = [];
            data.forEach(elem => {
                categories.push(elem[0]);
                pays.push(elem[1]);
            });

            Highcharts.chart(containerName, {
                chart: {
                    type: 'bar'
                },

                title: {
                    text: null
                },

                plotOptions: {
                    bar: {
                        dataLabels: {
                            align: "center"
                        }
                    }
                },

                xAxis: {
                    categories: categories,
                    labels: {
                        enabled: xAxisLabels
                    },
                    title: {
                        text: 'SIC Section',
                        enabled: yAxisTitle
                    },
                    type: 'category'
                },

                yAxis: {
                    title: {
                        text: 'Median Pay',
                        enabled: yAxisTitle
                    },
                    labels: {
                        format: '{value}%'
                    },
                    plotLines: [{
                        value: 0,
                        width: 2,
                        color: 'black',
                        zIndex: 10
                    }]
                },

                series: [{
                    data: pays,
                    showInLegend: false,
                    negativeColor: 'Red',
                    color: 'Green',
                    name: 'Pay Gap'
                }]
            })
        })
    })
}

function draw_heatmap(containerName, filters) {
    fetch(form_api_url(containerName, filters)).then(resp => {

        const isPreview = (containerName.substring(1, 6) === "chart");

        resp.json().then(data => {

            var data2 = [];
            data.forEach(row => {
                data2.push([row[0], row[2]]);
            });
            // console.log(data2);

            $.getJSON("/static/ukcounties.json", function(geojson) {

                // console.log(geojson);

                Highcharts.mapChart(containerName, {
                    chart: {
                        map: geojson
                    },
            
                    title: {
                        text: null
                    },
            
                    accessibility: {
                        typeDescription: 'Map of the United Kingdom.'
                    },
            
                    mapNavigation: {
                        enabled: isPreview,
                        buttonOptions: {
                            verticalAlign: 'bottom'
                        }
                    },

                    legend: {
                        enabled: isPreview,
                        layout: 'vertical',
                        align: 'right',
                        verticalAlign: 'middle',
                        itemMarginTop: 10,
                        itemMarginBottom: 10
                    },
            
                    colorAxis: {
                        stops: [
                            [0, '#c4463a'],
                            [0.5, '#e6ffee'],
                            [0.9, '#009933']
                        ],
                        min: -15
                    },
            
                    series: [{
                        data: data2,
                        keys: ['name', 'value'],
                        joinBy: 'name',
                        name: 'Pay Gap',
                        color: 'Green',
                        tooltip: {
                            valueSuffix: '%'
                        }
                    }]
                });
            });       
        });
    })
}

function draw_plot_size(containerName, filters) {
    fetch(form_api_url(containerName, filters)).then(resp => {
        resp.json().then((data) => {
            // console.log(data);

            const isPreview = (containerName.substring(1, 6) === "chart");

            var categories = [];
            var pays = [];
            data.forEach(elem => {
                categories.push(elem[0]);
                pays.push(elem[2]);
            });

            Highcharts.chart(containerName, {
                chart: {
                    type: 'column'
                },

                title: {
                    text: null
                },

                xAxis: {
                    categories: categories,
                    categories: categories,
                    labels: {
                        enabled: isPreview
                    },
                    title: {
                        text: 'Number of Employees',
                        enabled: isPreview
                    },
                },

                yAxis: {
                    title: {
                        text: 'Median Pay',
                        enabled: isPreview
                    },
                    labels: {
                        format: '{value}%'
                    },
                    plotLines: [{
                        value: 0,
                        width: 2,
                        color: 'black',
                        zIndex: 10
                    }]
                },

                series: [{
                    data: pays,
                    lineWidth: 4,
                    showInLegend: false,
                    name: "Pay Gap",
                    color: 'Green',
                    threshold: 0,
                    negativeColor: 'Red',
                }]
            });
        });
    })
}

function draw_plot_type(containerName, filters) {
    fetch(form_api_url(containerName, filters)).then(resp => {
        resp.json().then((data) => {
            console.log(data);

            const isPreview = (containerName.substring(1, 6) === "chart");

            var categories = [];
            var pays = [];
            data.forEach(elem => {
                categories.push(elem[0]);
                pays.push(elem[1]);
            });

            Highcharts.chart(containerName, {
                chart: {
                    type: 'bar'
                },

                title: {
                    text: null
                },

                plotOptions: {
                    bar: {
                        dataLabels: {
                            align: "center"
                        }
                    }
                },

                xAxis: {
                    categories: categories,
                    labels: {
                        enabled: isPreview
                    },
                    title: {
                        text: 'Employer Type',
                        enabled: isPreview
                    },
                    type: 'category'
                },

                yAxis: {
                    title: {
                        text: 'Median Pay',
                        enabled: isPreview
                    },
                    labels: {
                        format: '{value}%'
                    },
                    plotLines: [{
                        value: 0,
                        width: 2,
                        color: 'black',
                        zIndex: 10
                    }]
                },

                series: [{
                    data: pays,
                    showInLegend: false,
                    negativeColor: 'Red',
                    color: 'Green',
                    name: 'Pay Gap'
                }]
            })
        })
    });
}