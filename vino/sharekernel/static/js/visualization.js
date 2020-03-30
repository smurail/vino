class Visualization {
    constructor(element) {
        this.element = element instanceof HTMLElement ?
                       element :
                       document.querySelector(element);
        this.update();
    }

    loading(isLoading) {
        var loader = this.element.querySelector('.loader');
        loader.classList.toggle('visible', isLoading);
    }

    plot(data) {
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
    }

    load(onLoad) {
        var url = this.element.querySelector('input[name=url]');
        this.loading(true);
        fetch(url.value)
            .then(r => r.json())
            .then(data => onLoad(data))
            .catch(error => console.log(error))
            .finally(() => this.loading(false));
    }

    update() {
        this.load(this.plot.bind(this));
    }
}
