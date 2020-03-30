"use strict";

class Visualization {
    constructor(element) {
        this.element = element instanceof HTMLElement ?
                       element :
                       document.querySelector(element);
        this.loader = this.element.querySelector('.loader');
        setTimeout(this.load.bind(this), 1);
    }

    dispatchEvent(name, details) {
        this.element.dispatchEvent(new CustomEvent(name, details));
    }

    addEventListener(name, callback) {
        this.element.addEventListener(name, callback);
    }

    loading(isLoading) {
        this.loader.classList.toggle('visible', isLoading);
    }

    plot(data) {
        this.dispatchEvent('plotstart', {data: data});

        var view = this.element.querySelector('.view'),
            layout = {
                bargap: 0,
                xaxis: { title: data.xtitle },
                yaxis: { title: data.ytitle }
            },
            trace = {
                type: 'bar',
                orientation: 'h'
            };


        for (const p in data)
            trace[p] = data[p];

        Plotly.react(view, [trace], layout);

        this.dispatchEvent('plotend');
    }

    load() {
        this.dispatchEvent('load');
        this.loading(true);
        var url = this.element.querySelector('input[name=url]');
        fetch(url.value)
            .then(r => r.json())
            .then(data => this.plot(data))
            .catch(error => console.log(error))
            .finally(() => this.loading(false));
    }
}
