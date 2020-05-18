"use strict";

const ASYNC_DELAY = 50;

class Visualization extends EventTarget {
    constructor(element, options) {
        super();
        options = options || {};
        this.element = element instanceof HTMLElement ?
                       element :
                       document.querySelector(element);
        this.loader = this.element.querySelector('.loader');
        this.options = {
            showShapes: options.showShapes || false
        };
    }

    dispatchCustomEvent(name, details) {
        this.dispatchEvent(new CustomEvent(name, details));
    }

    loading(isLoading) {
        this.loader.classList.toggle('visible', isLoading);
    }

    plot(data) {
        this.data = data = data || this.data;
        this.dispatchCustomEvent('plotstart', {data: data});

        var threeDimensional = data.variables.length > 2 ? true : false,
            view = this.element.querySelector('.view'),
            layout = {
                margin:
                    threeDimensional ?
                    { t: 0, r: 0, b: 0, l: 0 } :
                    { t: 20, r: 0, b: 70, l: 80 },
                hovermode: false,
                modebar: {
                    bgcolor: 'rgba(255,255,255,0.9)'
                },
                bargap: 0, // used when trace.type == 'bar'
                xaxis: { title: data.variables[0].fullname },
                yaxis: { title: data.variables[1].fullname },
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
                responsive: true,
                scrollZoom: true
            };

        if (data.rectangles && !this.shapes)
            this.shapes = data.rectangles.map(r => (
                {
                    type: 'rect',
                    x0: r[0], y0: r[2],
                    x1: r[1], y1: r[3],
                    line: { width: 0.2 }
                }
            ));

        if (this.options.showShapes && this.shapes)
            layout.shapes = this.shapes;

        if (threeDimensional) {
            layout.scene = {
                xaxis: { title: data.variables[0].name },
                yaxis: { title: data.variables[1].name },
                zaxis: { title: data.variables[2].name }
            }
        } else {
            layout.dragmode = 'pan';
        }

        for (const p in data)
            trace[p] = data[p];

        Plotly.react(view, [trace], layout, config);

        this.dispatchCustomEvent('plotend');
    }

    load(url) {
        this.dispatchCustomEvent('load');
        this.loading(true);
        this.shapes = null;
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

        this.id = element.getAttribute('data-id');
        this.form = this.element.querySelector('form');
        this.kernel = this.form.elements['kernel'];
        this.reload = this.form.querySelector('button');
        this.showShapes = document.getElementById('show-shapes-' + this.id);

        this.options.showShapes = this.showShapes.checked;

        this.addEventListener('load', e => {
            this.kernel.disabled = this.reload.disabled = true;
        });
        this.addEventListener('plotend', e => {
            this.kernel.disabled = this.reload.disabled = false;
        });
        this.form.addEventListener('submit', e => {
            this.load();
            e.preventDefault();
        });
        this.kernel.addEventListener('change', e => this.load());
        this.showShapes.addEventListener('change', e => this.updateShapes());

        setTimeout(this.load.bind(this), ASYNC_DELAY);
    }

    updateShapes() {
        this.options.showShapes = this.showShapes.checked;
        this.loading(true);
        setTimeout(() => {
            this.plot();
            this.loading(false);
        }, ASYNC_DELAY);
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
