"use strict";

//           ______     ___________            _____            ______
//   ___________  /_______  /___  /____  __    __  /_______________  /_______
//   ___  __ \_  /_  __ \  __/_  /__  / / /    _  __/  __ \  __ \_  /__  ___/
//   __  /_/ /  / / /_/ / /_ _  / _  /_/ /     / /_ / /_/ / /_/ /  / _(__  )
//   _  .___//_/  \____/\__/ /_/  _\__, /      \__/ \____/\____//_/  /____/
//   /_/                          /____/

function marker(color, size) {
    return {
        size: size || 2,
        color: color == null ? null : color,
        colorscale: 'Viridis',
        reversescale: true
    }
}

function line(color, width) {
    return {
        width: width || 1,
        color: color == null ? null : color
    };
}

function points2d(x, y, color, size) {
    return {
        type: 'scattergl',
        mode: 'markers',
        marker: marker(color, size),
        x: x,
        y: y
    }
}

function points3d(x, y, z, color, size) {
    return {
        type: 'scatter3d',
        mode: 'markers',
        marker: marker(color, size),
        x: x,
        y: y,
        z: z
    }
}

function points(x, y, z, color, size) {
    return z == null ?
           points2d(x, y, color, size) :
           points3d(x, y, z, color, size);
}

function shapes(x, y, color, width) {
    return {
        type: 'scattergl',
        mode: 'lines',
        hoverinfo: 'skip',
        connectgaps: false,
        line: line(color, width),
        x: x,
        y: y
    };
}

function layoutGrid(info) {
    const min = info.grid ? info.grid.bounds[0] : null,
          unit = info.grid ? info.grid.unit : null,
          labels = false;

    return min == null || unit == null ? null : {
        'xaxis.tick0': min[0],
        'xaxis.dtick': unit[0],
        'xaxis.showticklabels': labels,
        'yaxis.tick0': min[1],
        'yaxis.dtick': unit[1],
        'yaxis.showticklabels': labels
        //xaxis: {tick0: min[0], dtick: unit[0], showticklabels: labels},
        //yaxis: {tick0: min[1], dtick: unit[1], showticklabels: labels}
    }
}

function layoutRanges(info) {
    const axes = info.axes;

    if (!Array.isArray(axes))
        return null;

    if (axes.length == 2) {
        return {
            'xaxis.range': axes[0].range,
            'yaxis.range': axes[1].range
        }
    } else {
        return {
            'scene.xaxis.range': axes[0].range,
            'scene.yaxis.range': axes[1].range,
            'scene.zaxis.range': axes[2].range,
        }
    }
}

function layout2d(info) {
    function label(axis) {
        let a = info.axes[axis];
        return a.name + (a.desc ? ` (${a.desc})` : '');
    }

    return {
        dragmode: 'pan',
        hovermode: 'closest',
        margin: {t: 50, r: 50},
        xaxis: {title: label(0)},
        yaxis: {title: label(1)}
    }
}

function layout3d(info) {
    function label(axis) {
        let a = info.axes[axis]
        return `[${a.axis}] ${a.name}`;
    }

    return {
        hovermode: 'closest',
        margin: {t: 0, r: 0, b: 0, l: 0},
        scene: {
            xaxis: {title: label(0)},
            yaxis: {title: label(1)},
            zaxis: {title: label(2)}
        }
    }
}

function layout(info) {
    return info.dim == 2 ? layout2d(info) : layout3d(info);
}

//   _____       _____                         __________
//   ___(_)________  /__________________ ________  /___(_)____________________
//   __  /__  __ \  __/  _ \_  ___/  __ `/  ___/  __/_  /_  __ \_  __ \_  ___/
//   _  / _  / / / /_ /  __/  /   / /_/ // /__ / /_ _  / / /_/ /  / / /(__  )
//   /_/  /_/ /_/\__/ \___//_/    \__,_/ \___/ \__/ /_/  \____//_/ /_//____/
//

function speedUpWheel(factor) {
    if (factor == null)
        factor = 4;

    // https://github.com/plotly/plotly.js/issues/1085#issuecomment-564488236
    window.addEventListener('wheel', (event) => {
        if (!event.isTrusted) return;
        event.stopPropagation();
        if (event.shiftKey) return false;
        const newEv = new WheelEvent('wheel', {
                clientX: event.clientX,
                clientY: event.clientY,
                deltaY:  event.deltaY*factor
            });
        event.target.dispatchEvent(newEv);
    });
}

function hookFullscreen(element) {
    const vzId = element.dataset.id,
          btn = document.getElementById('fullscreen-' + vzId),
          view = element.querySelector('.vz-view');

    btn.addEventListener('click', e => {
        const cls = 'vz-fullscreen',
              isFullscreen = !document.body.classList.contains(cls),
              oldIcon = isFullscreen ? 'fa-expand' : 'fa-compress',
              newIcon = isFullscreen ? 'fa-compress' : 'fa-expand';

        // Toggle fullscreen class on body
        document.body.classList.toggle(cls);

        // Update fullscreen button icon
        btn.querySelector('.fas').classList.replace(oldIcon, newIcon);

        // Resize plotly view
        try {
            Plotly.relayout(view, {autosize: true});
        } catch {}
    });
}

function parsePPA(ppa) {
    if (typeof ppa === "number")
        return Math.floor(ppa);

    if (typeof ppa === "string")
        ppa = ppa.split(',').map(x => parseInt(x));

    if (Array.isArray(ppa))
        if (ppa.reduce((p, x) => p && !isNaN(x), true))
            return ppa.length == 1 ? ppa[0] : ppa;

    return NaN;
}

// Borrowed from https://stackoverflow.com/a/45813619
function combinations(array, size) {
    var result = [];

    function p(t, i) {
        if (t.length === size) {
            result.push(t);
            return;
        }
        if (i + 1 > array.length)
            return;
        p(t.concat(array[i]), i + 1);
        p(t, i + 1);
    }

    p([], 0);
    return result;
}

function hookVisualization(element) {
    const vzId = element.dataset.id,
          form = element.querySelector('form'),
          sectionForm = element.querySelectorAll('form')[1],
          fields = {
              vino: form.elements['kernel'],
              format: form.elements['format'],
              ppa: form.elements['ppa'],
              plane: document.getElementById('plane-' + vzId),
              section: form.elements['show-section'],
              distances: form.elements['show-distances'],
              shapes: form.elements['show-shapes']
          },
          switchPlaneButton = document.getElementById('switch-plane-' + vzId),
          infos = new Map();

    let state = {};

    function getRequestedState() {
        let at = null;

        if (fields.section.checked) {
            const inputs = sectionForm.querySelectorAll('.axis-container input[type="range"]');
            at = Array.from(inputs).map(input => input.value).join(',');
        }

        return {
            id: parseInt(fields.vino.value),
            format: fields.format.value,
            ppa: parsePPA(fields.ppa.value),
            section: fields.section.checked,
            plane: fields.plane.value,
            at: at,
            shapes: fields.shapes.checked
        };
    }

    function commitRequestedState() {
        state = getRequestedState();
    }

    function isDirty() {
        return JSON.stringify(state) !== JSON.stringify(getRequestedState());
    }

    function isValid() {
        const info = infos.get(state.id),
              ppa = parsePPA(fields.ppa.value);

        if (!fields.format.value || (Array.isArray(ppa) ? ppa.length == info.dim : ppa)) {
            fields.ppa.classList.remove('is-invalid');
        } else {
            fields.ppa.classList.add('is-invalid');
            return false;
        }

        return true;
    }

    function updateVino(info) {
        if (!info)
            info = infos.get(parseInt(fields.vino.value));

        if (info && isDirty() && isValid()) {
            commitRequestedState();

            console.log('PLOT', state);

            const id = info.id,
                  ppa = fields.ppa.value,
                  format = fields.format.value,
                  currentFormat = format || info.format,
                  apiFormat = ({'bars': 'bargrid', 'regulargrid': 'regulargrid'})[format] || null,
                  hasShapes = info.dim == 2 && [FORMAT_BARGRID, FORMAT_KDTREE].indexOf(currentFormat) >= 0,
                  conv = apiFormat ? `/${apiFormat}/${ppa}` : '',
                  plane = state.plane,
                  at = state.at;

            console.log('SHOW', id, conv, fields.shapes.checked && hasShapes ? 'with shapes' : 'without shapes');

            let plot = vinoPlot();

            if (fields.shapes.checked && hasShapes)
                plot = plot.trace(`/api/vino/${id}${conv}/shapes/`);

            if (fields.section.checked) {
                plot = plot.trace(`/api/vino/${id}${conv}/section/${plane}/${at}/`)
                           .relayout(layoutRanges);
            } else {
                plot = plot.trace(`/api/vino/${id}${conv}/`)
            }

            plot.show();
        }
    }

    function updateSectionAxes(info) {
        const plane = fields.plane.value.split(',').map(x => parseInt(x)),
              axes = info.axes.filter(a => !plane.includes(a.order)),
              _ppa = parsePPA(fields.ppa.value),
              ppa = Array.isArray(_ppa) ? _ppa : Array(info.dim).fill(_ppa),
              container = document.getElementById('axis-container-' + vzId),
              oldContainers = container.parentNode.querySelectorAll('.axis-container');

        console.log('updateAxes', info.grid, axes, ppa, container, container.parentNode, oldContainers);

        for (let old of oldContainers)
            container.parentNode.removeChild(old);

        axes.forEach(a => {
            const node = container.cloneNode(true),
                  label = node.querySelector('label'),
                  range = node.querySelector('input[type="range"]'),
                  input = node.querySelector('input[type="number"]');

            node.classList.remove('d-none');
            node.classList.add('axis-container');
            label.textContent = a.name;
            range.max = ppa[a.order]-1;

            range.addEventListener('change', e => {
                updateVino();
            });

            container.parentNode.insertBefore(node, null);
        });
    }

    function updateSectionPlanes(info) {
        const plane = document.getElementById('plane-' + vzId);

        plane.options.length = 0;

        combinations(info.axes, 2).forEach((p, i) => {
            const label = p.map(a => a.name).join(', '),
                  value = p.map(a => a.order).join(',')

            plane.appendChild(new Option(label, value));
        });
    }

    function updateForm(info) {
        const defaultFormat = FORMAT_BARGRID,
              defaultPPA = info.dim == 2 ? 1000 : 50,
              elementPPA = fields.ppa.parentNode.parentNode;

        console.log('updateForm', state, getRequestedState());

        if (fields.vino.value != state.id) {
            fields.format.value = defaultFormat;
            fields.ppa.value = defaultPPA;
        }

        fields.section.disabled = info.dim <= 2 || info.dim > 3;
        if (info.dim > 3) {
            fields.section.checked = true;
            bootstrap.Collapse.getOrCreateInstance('#section-chooser-' + vzId).show();
        }
        if (info.dim > 2 && fields.section.checked != state.section) {
            fields.format.value = fields.section.checked ? FORMAT_REGULARGRID : defaultFormat;
            fields.format.disabled = fields.section.checked;
        }

        const currentFormat = fields.format.value;

        elementPPA.style.display = currentFormat ? '' : 'none';
        if (currentFormat != state.format) {
            if (currentFormat == FORMAT_BARGRID)
                fields.ppa.value = info.dim == 2 ? 1000 : 50;
            else if (currentFormat == FORMAT_REGULARGRID)
                fields.ppa.value = info.dim == 2 ? 300 : 30;
        }

        fields.shapes.disabled = info.dim != 2 || ![FORMAT_BARGRID, FORMAT_KDTREE].includes(currentFormat || info.format);

        if (fields.section.checked != state.section) {
            updateSectionPlanes(info);
            updateSectionAxes(info);
        } else if (fields.section.checked && (fields.plane.value != state.plane || fields.ppa.value != state.ppa)) {
            updateSectionAxes(info);
        }

        updateVino(info);
    }

    function showVino(vinoId) {
        if (typeof vinoId !== "string" && typeof vinoId !== "number")
            vinoId = fields.vino.value;

        vinoId = parseInt(vinoId);

        if (isNaN(vinoId))
            return;

        const info = infos.get(vinoId);

        if (!info) {
            fetch(`/api/vino/${vinoId}/info/`)
                .then(r => r.json())
                .then(info => infos.set(vinoId, info).get(vinoId))
                .then(info => updateForm(info));
        } else {
            updateForm(info);
        }
    }

    switchPlaneButton.addEventListener('click', () => {
        const opt = fields.plane.options[fields.plane.selectedIndex];
        opt.value = opt.value.split(',').reverse().join(',');
        opt.label = opt.label.split(', ').reverse().join(', ');
        showVino();
    });

    fields.format.addEventListener('change', showVino);
    fields.section.addEventListener('change', showVino);
    fields.plane.addEventListener('change', showVino);

    form.addEventListener('submit', e => {
        e.preventDefault();
        showVino();
    });
    fields.vino.addEventListener('change', showVino);
    fields.shapes.addEventListener('change', showVino);
    showVino();
}

//          _____                          ______     _____
//   ___   ____(_)____________     ___________  /_______  /_
//   __ | / /_  /__  __ \  __ \    ___  __ \_  /_  __ \  __/
//   __ |/ /_  / _  / / / /_/ /    __  /_/ /  / / /_/ / /_
//   _____/ /_/  /_/ /_/\____/     _  .___//_/  \____/\__/
//                                 /_/

function getElement(element) {
    return typeof element === 'string' || element instanceof String ?
           document.querySelector(element) :
           element;
}

const PLOTLY_DEFAULT_CONFIG = {
    responsive: true,
    scrollZoom: true
};

const FORMAT_BARGRID = 'bars',
      FORMAT_POLYGON = 'polygon',
      FORMAT_REGULARGRID = 'regulargrid',
      FORMAT_KDTREE = 'kdtree';

const INFO_PROPERTIES = [
    'id', 'vp', 'title', 'dim', 'format', 'size', 'axes', 'original', 'grid'
];

class VinoPlot {
    constructor(element, config) {
        if (config == null)
            config = PLOTLY_DEFAULT_CONFIG;

        this.promises = [];
        this.postprocess = [];
        this.config = config;
        this.info = {};

        this.element = getElement(element);
        this.view = getElement('.vz-view');
        this.loader = getElement('.vz-loader');
    }

    error(msg) {
        console.log('ERROR:', msg);
    }

    loading(isLoading) {
        document.body.classList.toggle('loading', isLoading);
        this.loader.classList.toggle('visible', isLoading);
        // XXX Ugly HACK
        const fieldset = this.element.parentNode.parentNode.querySelector('fieldset');
        if (fieldset) fieldset.disabled = isLoading;
    }

    toTrace(data) {
        const color = '#80d0d0',
              size = data.format == FORMAT_REGULARGRID ? 3 : null;
        let V, trace;

        if ((V = data.shapes))
            trace = shapes(V[0], V[1], color);
        else if ((V = data.values))
            trace = points(V[0], V[1], V[2], V[2] || V[1], size);

        if (data.format == FORMAT_POLYGON) {
            trace.mode = 'lines+markers';
            trace.line = {width: 1, dash: "dash"};
        }

        return trace;
    }

    clean() {
        Plotly.purge(this.view);
        return this;
    }

    keepInfo(chunks) {
        for (let data of chunks)
            for (let p of INFO_PROPERTIES)
                if (data.hasOwnProperty(p))
                    this.info[p] = data[p];
        return this;
    }

    plot(chunks) {
        const traces = chunks.map(data => this.toTrace(data));
        Plotly.react(this.view, traces, layout(chunks[0]), this.config);
        return this;
    }

    after(callback) {
        this.postprocess.push(callback);
        return this;
    }

    relayout(callback) {
        return this.after(
            () => Plotly.relayout(this.view, callback(this.info))
        );
    }

    fetch(url, callback) {
        let promise = fetch(url).then(r => r.json()).then(callback);
        return this;
    }

    trace(url/*, urlN...*/) {
        let requests = Array.from(arguments).map(url => fetch(url));
        this.promises = this.promises.concat(requests);
        return this;
    }

    show() {
        let p;

        this.loading(true);
        p = Promise.all(this.promises)
            .then(results => Promise.all(results.map(r => r.json())))
            .then(chunks => this.plot(chunks).keepInfo(chunks))
            .then(data => this.postprocess.forEach(fn => fn.call(this, data)))
            .catch(error => console.log('ERROR FETCHING:', error))
            .finally(() => this.loading(false));

        return this;
    }
}

function vinoPlot(view) {
    return new VinoPlot(view == null ? '.vz-view' : view);
}

//               _____
//   ______________  /____  _________
//   __  ___/  _ \  __/  / / /__  __ \
//   _(__  )/  __/ /_ / /_/ /__  /_/ /
//   /____/ \___/\__/ \__,_/ _  .___/
//                           /_/
//

window.addEventListener('DOMContentLoaded', () => {
    const containers = document.querySelectorAll('.vz-container');
    containers.forEach(hookFullscreen);
    containers.forEach(hookVisualization);
    speedUpWheel(4);
});
