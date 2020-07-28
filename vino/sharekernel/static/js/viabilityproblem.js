const HASH_ROUTE = /#kernel\/(\d+)(?:\/ppa\/(\d+))?\/?/,
      HASH_ROUTE_URL = (id, ppa) => '#kernel/'+id+(ppa?'/ppa/'+ppa:'')+'/';

function selectKernel(id, ppa=null) {
    if (!id) return;
    var currentPPA = $('input[name=ppa]');
    // Setup PPA if any
    if ((ppa = parseInt(ppa))) {
        currentPPA.val(ppa);
    } else {
        ppa = currentPPA.val();
    }
    // Check the checkbox and triggers change event to visualize it
    $('#select-kernel-' + id)
        .prop('checked', true)
        .trigger('change');
    // Change URL hash
    location.hash = HASH_ROUTE_URL(id, ppa);
}

$(function() {
    var kernels = $('#kernels-table tr[data-kernel-id]'),
        checkboxes = $('#kernels-table input[type=checkbox]'),
        currentKernel = $('.vz-container *[name=kernel]'),
        visualizations = $('.vz-container'),
        doc = $('html, body'),
        ppa = null,
        args, kernelId;

    // If there is only one kernel, disable the checkbox
    if (kernels.length == 1) {
        checkboxes.prop('disabled', true);
    } else {
        // Visualization loading can't be interrupted for now, as a workaround
        // disable all checkboxes while a kernel is loading
        visualizations.each((_, el) => {
            el.vz.addEventListener('load', () => checkboxes.prop('disabled', true));
            el.vz.addEventListener('plotend', () => checkboxes.prop('disabled', false));
        });
    }

    // Attach change event to each kernel checkbox
    checkboxes.on('change', function() {
        var cb = $(this),
            row = cb.closest('tr'),
            kernelId = row.data('kernel-id');

        // Unselect all rows but changed row
        checkboxes.not(this).prop('checked', false)
            .closest('tr').removeClass('table-primary');

        // Colorize changed row in any case:
        // - Handles page reload
        // - Once visualized a kernel can't be "unvisualized"
        row.addClass('table-primary');

        // Update visualization if needed
        if (currentKernel.val() != kernelId) {
            // Change current kernel
            currentKernel.val(kernelId);
            // Trigger change event with DOM style (see visualize.js)
            currentKernel[0].dispatchEvent(new Event('change'));
        }
    });

    // Other way around: attach change event to kernel chooser
    currentKernel.on('change', function() {
        selectKernel(currentKernel.val());
    });

    // Update hash when user change PPA
    visualizations[0].vz.addEventListener('load', (e) => {
        location.hash = HASH_ROUTE_URL(
            visualizations[0].vz.kernel.value,
            visualizations[0].vz.ppa.value
        );
    });

    // Select and show kernel in hash or fallback to first
    if ((args = location.hash.match(HASH_ROUTE))) {
        kernelId = args[1], ppa = args[2];
        if (doc.scrollTop() == 0)
            doc.scrollTop($('#kernels').offset().top);
    } else {
        kernelId = kernels.first().data('kernel-id');
    }
    selectKernel(kernelId, ppa);
});
