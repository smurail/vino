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
                margin: { t: 60, r: 20, b: 80, l: 80, pad: 0 },
                bargap: 0, // used when trace.type == 'bar'
                xaxis: { title: data.xtitle },
                yaxis: { title: data.ytitle },
                dragmode: 'pan'
            },
            trace = {
                base: 0, // used when trace.type == 'bar'
                orientation: 'h', // used when trace.type == 'bar'
                type: 'z' in data ? 'scatter3d' : 'scattergl',
                mode: 'markers',
                marker: {
                    size: 2
                }
            },
            config = {
                scrollZoom: true
            };

        if (data.rectangles)
            layout.shapes = data.rectangles.map(r => (
                {
                    type: 'rect',
                    x0: r[0], y0: r[2],
                    x1: r[1], y1: r[3],
                    line: { width: 0.2 }
                }
            ))

        if (data.ztitle)
            layout.zaxis = { title: data.ztitle };

        for (const p in data)
            trace[p] = data[p];

        Plotly.react(view, [trace], layout, config);

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

class KernelVisualization extends Visualization {
    constructor(element) {
        super(element);
        this.form = this.element.querySelector('form');
        this.kernel = this.form.elements['kernel'];
        this.button = this.form.querySelector('button');
        this.addEventListener('load', e => {
            this.kernel.disabled = this.button.disabled = true;
        });
        this.addEventListener('plotend', e => {
            this.kernel.disabled = this.button.disabled = false;
        });
        this.form.addEventListener('submit', e => {
            this.load();
            e.preventDefault();
        });
        this.kernel.addEventListener('change', e => this.load());
        setTimeout(this.load.bind(this), 1);
    }

    url(pk) {
        return URL_KERNEL_DATA(pk);
    }

    load() {
        super.load(this.url(this.kernel.value));
    }
}

// https://github.com/plotly/plotly.js/issues/1085#issuecomment-564488236
window.addEventListener('wheel', (event) => {
    if (!event.isTrusted) return;
    event.stopPropagation();
    if (event.shiftKey) return false;
    var newEv = new WheelEvent('wheel', {
            clientX: event.clientX,
            clientY: event.clientY,
            deltaY:  event.deltaY*4
        });
    event.target.dispatchEvent(newEv);
});

document.addEventListener('DOMContentLoaded', () => {
    document
        .querySelectorAll('.kernel')
        .forEach((element) => new KernelVisualization(element));
});
