var tableToIcon = {
    'software': 'microchip',
    'dataformat': 'database'
};

function getInstance(subject) {
    var bits = subject.split(':'),
        table = bits[0],
        pk = bits[1];

    if (!table || !database.hasOwnProperty(table) || !pk)
        return null;

    return Object.assign({$table: table}, database[table][pk]);
}

function formatTitle(o) {
    return o.$table == 'dataformat' ? `Data format "${o.title}"` : o.title;
}

function formatContent(o) {
    var content = '',
        field = title => `<span class="text-muted">${title}:</span> `;

    if (o.description)
        content += `<p class="description text-justify">${o.description}</p>`;
    if (o.publication)
        content += `<p>${field('Publication')}<em>${o.publication}</em></p>`;
    if (o.author)
        content += `<p>${field('Author')}${o.author}</p>`;
    if (o.email)
        content += `<p>${field('Email')}<a href="mailto:${o.email}">${o.email}</a></p>`;
    if (o.url)
        content += `<p>${field('Website')}<a href="${o.url}" target="_blank">${o.url}</a></p>`;
    if (o.version)
        content += `<p>${field('Version')}${o.version}</p>`;
    if (o.parameters)
        content += `<p>${field('Parameters')}${o.parameters}</p>`;

    return content.replace(/(|\S)([,;])(\S)/gi, '$1$2 $3');
}

function getContext(subject) {
    var instance = getInstance(subject);

    return {
        icon: tableToIcon[instance.$table] || 'info-circle',
        title: formatTitle(instance),
        content: formatContent(instance)
    };
}

$('#modal').on('show.bs.modal', function (event) {
    var button = $(event.relatedTarget),
        subject = button.data('subject'),
        modal = $(this);

    with (getContext(subject)) {
        modal.find('.modal-title').html(`<i class="fas fa-${icon}"></i> ${title}`);
        modal.find('.modal-body').html(content);
    }
})
