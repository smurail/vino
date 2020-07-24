const HASH_PREFIX = '#kernel/';

function selectKernel(id) {
    if (!id) return;
    // Check the checkbox and triggers change event to visualize it
    $('#select-kernel-' + id)
        .prop('checked', true)
        .trigger('change');
    // Change URL hash
    location.hash = HASH_PREFIX + id;
}

$(function() {
    var kernels = $('#kernels-table tr[data-kernel-id]'),
        checkboxes = $('#kernels-table input[type=checkbox]'),
        currentKernel = $('.vz-container *[name=kernel]'),
        visualizations = $('.vz-container'),
        kernelId;

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

    // Select and show kernel in hash or fallback to first
    if (location.hash.startsWith(HASH_PREFIX)) {
        kernelId = location.hash.substring(HASH_PREFIX.length);
        $('html, body').scrollTop($('#kernels').offset().top);
    } else {
        kernelId = kernels.first().data('kernel-id');
    }
    selectKernel(kernelId);
});
