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
        if (!this.defaultCursor)
            this.defaultCursor = document.body.style.cursor || 'default';
        document.body.style.cursor = isLoading ? 'wait' : this.defaultCursor;
        this.loader.classList.toggle('visible', isLoading);
    }

    plot(data) {
        var sameVP = !data || (this.data && this.data.vp == data.vp);

        this.data = data = data || this.data;
        this.dispatchCustomEvent('plotstart', {data: data});

        const AXES = ['x', 'y', 'z'];

        var threeDimensional = data.variables.length > 2 ? true : false,
            view = this.element.querySelector('.view'),
            plot = {
                layout: {
                    margin:
                        threeDimensional ?
                        { t: 0, r: 0, b: 0, l: 0 } :
                        { t: 20, r: 0, b: 70, l: 80 },
                    hovermode: 'closest',
                    modebar: {
                        bgcolor: 'rgba(255,255,255,0.9)'
                    },
                    xaxis: { title: data.variables[0].fullname },
                    yaxis: { title: data.variables[1].fullname },
                },
                data: [{
                    type: threeDimensional ? 'scatter3d' : 'scattergl',
                    mode: 'markers',
                    hoverinfo: AXES.slice(0, data.variables.length).join('+'),
                    showlegend: false,
                    marker: {
                        size: 2,
                        color: '#1f77b4' // muted blue
                    }
                }],
                config: {
                    responsive: true,
                    scrollZoom: true
                }
            },
            trace = plot.data[0],
            update = {};

        if (!threeDimensional && this.options.showShapes && data.rectangles) {
            plot.data.unshift({
                type: 'scattergl',
                mode: 'lines',
                hoverinfo: 'skip',
                showlegend: false,
                connectgaps: false,
                x: data.rectangles.flatMap(r => [
                    r[0], r[1], r[1], r[0], r[0], null
                ]),
                y: data.rectangles.flatMap(r => [
                    r[3], r[3], r[2], r[2], r[3], null
                ]),
                line: {
                    width: 1,
                    color: '#afeeee' // pale turquoise
                }
            });
        }

        if (threeDimensional) {
            plot.layout.scene = {
                xaxis: { title: data.variables[0].name },
                yaxis: { title: data.variables[1].name },
                zaxis: { title: data.variables[2].name }
            }
        } else {
            plot.layout.dragmode = 'pan';
        }

        for (var i in data.variables) {
            trace[AXES[i]] = data.variables[i].data;

            // Keep pan and zoom
            if (sameVP && view.layout && !threeDimensional) {
                var axis = AXES[i] + 'axis';
                update[axis+'.range[0]'] = view.layout[axis].range[0];
                update[axis+'.range[1]'] = view.layout[axis].range[1];
            }
        }

        // See https://plotly.com/javascript/plotlyjs-function-reference/#plotlynewplot
        Plotly.react(view, plot);

        if (update)
            Plotly.relayout(view, update);

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
