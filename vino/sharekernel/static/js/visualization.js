"use strict";

class Visualization extends EventTarget {
    constructor(element) {
        super();
        this.element = element instanceof HTMLElement ?
                       element :
                       document.querySelector(element);
        this.loader = this.element.querySelector('.loader');
    }

    dispatchCustomEvent(name, details) {
        this.dispatchEvent(new CustomEvent(name, details));
    }

    loading(isLoading) {
        this.loader.classList.toggle('visible', isLoading);
    }

    plot(data) {
        this.dispatchCustomEvent('plotstart', {data: data});

        var view = this.element.querySelector('.view'),
            layout = {
                bargap: 0, // used when trace.type == 'bar'
                xaxis: { title: data.xtitle },
                yaxis: { title: data.ytitle }
            },
            trace = {
                base: 0, // used when trace.type == 'bar'
                orientation: 'h', // used when trace.type == 'bar'
                type: 'z' in data ? 'scatter3d' : 'scattergl',
                mode: 'markers',
                marker: {
                    size: 2
                }
            };

        if (data.ztitle)
            layout.zaxis = { title: data.ztitle };

        for (const p in data)
            trace[p] = data[p];

        Plotly.react(view, [trace], layout);

        this.dispatchCustomEvent('plotend');
    }

    load(url) {
        this.dispatchCustomEvent('load');
        this.loading(true);
        fetch(url)
            .then(r => r.json())
            .then(data => this.plot(data))
            .catch(error => console.log(error))
            .finally(() => this.loading(false));
    }
}
