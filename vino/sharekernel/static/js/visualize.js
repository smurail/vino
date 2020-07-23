"use strict";

const ASYNC_DELAY = 50;
const AXES = ['x', 'y', 'z'];

window.addEventListener('DOMContentLoaded', () => {
    $('.vz-container').each((_, element) => new KernelVisualization(element));
});

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

// Safari doesn't allow to extend EventTarget, so implement a simple version
// Borrowed from https://developer.mozilla.org/fr/docs/Web/API/EventTarget
class EventDispatcher {
    constructor() {
        this.listeners = {};
    }

    addEventListener(type, callback) {
        if (!(type in this.listeners)) {
            this.listeners[type] = [];
        }
        this.listeners[type].push(callback);
    }

    removeEventListener(type, callback) {
        if (!(type in this.listeners)) {
            return;
        }
        var stack = this.listeners[type];
        for (var i = 0, l = stack.length; i < l; i++) {
            if (stack[i] === callback){
                stack.splice(i, 1);
                return;
            }
        }
    }

    dispatchEvent(event) {
        if (!(event.type in this.listeners)) {
            return true;
        }
        var stack = this.listeners[event.type];

        for (var i = 0, l = stack.length; i < l; i++) {
            stack[i].call(this, event);
        }
        return !event.defaultPrevented;
    }
}

class Visualization extends EventDispatcher {
    constructor(element, options) {
        super();
        options = options || {};
        this.element = element instanceof HTMLElement ?
                       element :
                       document.querySelector(element);
        this.loader = this.element.querySelector('.vz-loader');
        this.view = this.element.querySelector('.vz-view');
        this.options = {
            showShapes: options.showShapes || false
        };
    }

    dispatchCustomEvent(name, details) {
        this.dispatchEvent(new CustomEvent(name, details));
    }

    loading(isLoading) {
        document.body.classList.toggle('loading', isLoading);
        this.loader.classList.toggle('visible', isLoading);
    }

    plot(data) {
        var sameVP = !data || (this.data && this.data.vp == data.vp);

        this.data = data = data || this.data;
        this.dispatchCustomEvent('plotstart', {data: data});

        var threeDimensional = data.variables.length > 2 ? true : false,
            plot = {
                layout: {
                    margin:
                        threeDimensional ?
                        { t: 0, r: 0, b: 0, l: 0 } :
                        { t: 0, r: 0, b: 70, l: 80 },
                    hovermode: 'closest',
                    modebar: {
                        bgcolor: 'rgba(255,255,255,0.9)'
                    }
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
            plot.layout.xaxis = {
                title: data.variables[0].fullname,
            };
            plot.layout.yaxis = {
                title: data.variables[1].fullname,
                scaleanchor: 'x',
                scaleratio: 1
            };
            plot.layout.dragmode = 'pan';
        }

        for (var i in data.variables) {
            trace[AXES[i]] = data.variables[i].data;

            // Keep pan and zoom
            if (sameVP && this.view.layout && !threeDimensional) {
                var axis = AXES[i] + 'axis';
                update[axis+'.range[0]'] = this.view.layout[axis].range[0];
                update[axis+'.range[1]'] = this.view.layout[axis].range[1];
            }
        }

        if (sameVP && this.view.layout && threeDimensional) {
            update['scene.camera'] = this.view._fullLayout.scene._scene.getCamera();
        }

        // See https://plotly.com/javascript/plotlyjs-function-reference/#plotlynewplot
        Plotly.react(this.view, plot);

        if (update)
            Plotly.relayout(this.view, update);

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
        this.ppa = this.form.elements['ppa'];
        this.reload = this.form.querySelector('button') || {};
        this.showShapes = document.getElementById('show-shapes-' + this.id);
        this.fullscreen = document.getElementById('fullscreen-' + this.id);

        this.options.showShapes = this.showShapes.checked;

        this.addEventListener('load', e => {
            this.kernel.disabled = this.reload.disabled = this.ppa.disabled = this.showShapes.disabled = true;
        });
        this.addEventListener('plotend', e => {
            this.kernel.disabled = this.reload.disabled = this.ppa.disabled = this.showShapes.disabled = false;
            if (this.data) {
                if (this.data.originalFormat != 'kdtree')
                    this.ppa.disabled = true;
                if (this.data.variables.length > 2)
                    this.ppa.disabled = this.showShapes.disabled = true;
            }
            if (this.ppa.disabled)
                this.ppa.value = null;
        });
        this.form.addEventListener('submit', e => {
            this.load();
            e.preventDefault();
        });
        this.kernel.addEventListener('change', e => this.load());
        this.showShapes.addEventListener('change', e => this.updateShapes());
        this.fullscreen.addEventListener('click', e => {
            var cls = 'vz-fullscreen',
                isFullscreen = !this.element.classList.contains(cls),
                oldIcon = isFullscreen ? 'fa-expand' : 'fa-compress',
                newIcon = isFullscreen ? 'fa-compress' : 'fa-expand',
                axis, i;

            // Toggle fullscreen class
            this.element.classList.toggle(cls);
            this.fullscreen.querySelector('.fas').classList.replace(oldIcon, newIcon);

            // Plotly seems to change zoom when resizing view, to workaround
            // this issue save pan and zoom and restore it when exiting
            // fullscreen
            if (isFullscreen) {
                // Backup zoom and pan
                this.save = {vp: this.data.vp};
                for (i in AXES) {
                    axis = AXES[i] + 'axis';
                    if (this.view.layout[axis]) {
                        this.save[axis+'.range[0]'] = this.view.layout[axis].range[0];
                        this.save[axis+'.range[1]'] = this.view.layout[axis].range[1];
                    }
                }
                Plotly.Plots.resize(this.view);
            } else if (this.save && this.save.vp == this.data.vp) {
                // Restore zoom and pan if VP hasn't changed
                var update = {}
                for (i in this.save)
                    update[i] = this.save[i];
                Plotly.relayout(this.view, update);
                //Plotly.Plots.resize(this.view);
            }
        });

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
        var ppa = this.ppa.value ? this.ppa.value + '/' : ''
        return URL_KERNEL_DATA(pk) + ppa;
    }

    load() {
        super.load(this.url(this.kernel.value));
    }
}
