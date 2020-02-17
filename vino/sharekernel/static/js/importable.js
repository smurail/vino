function humanFileSize(bytes, si) {
    var thresh = si ? 1000 : 1024;
    if (Math.abs(bytes) < thresh) {
        return bytes + ' B';
    }
    var units = si
        ? ['kB','MB','GB','TB','PB','EB','ZB','YB']
        : ['KiB','MiB','GiB','TiB','PiB','EiB','ZiB','YiB'];
    var u = -1;
    do {
        bytes /= thresh;
        ++u;
    } while(Math.abs(bytes) >= thresh && u < units.length - 1);
    return bytes.toFixed(1)+' '+units[u];
}

(function($) {
    $(document).ready(function() {
        var title = $('#django-admin-importable').data('title');
        $('input[type="file"]').each(function() {
            if (this.multiple) {
                this.addEventListener('change', function() {
                    var feedback = $('<div class="inline-group tabular inline-related last-related feedback"><h2>'+title+'</h2></div>'),
                        fieldset = $('<fieldset class="module"/>').appendTo(feedback),
                        table = $('<table/>').appendTo(fieldset),
                        previous = $(this).closest('fieldset'),
                        cls, row, file, caption;
                    for (var i = 0; i < this.files.length; i++) {
                        cls = i % 2 == 0 ? 'row1' : 'row2';
                        row = $('<tr/>').addClass(cls).appendTo(table);
                        file = this.files[i];
                        caption = file.name+' ('+humanFileSize(file.size)+')';
                        $('<td/>').text(caption).appendTo(row);
                    }
                    previous.next('.feedback').remove();
                    previous.after(feedback);
                });
            }
        });
    });
})(django.jQuery);
