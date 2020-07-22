function selectKernel(id) {
    // Check the checkbox and triggers change event to visualize it
    $('#select-kernel-' + id)
        .prop('checked', true)
        .trigger('change');
}

$(function() {
    var kernels = $('#kernels tr[data-kernel-id]'),
        checkboxes = $('#kernels input[type=checkbox]'),
        currentKernel = $('.vz-container input[name=kernel]');

    // If there is only one kernel, disable the checkbox
    if (kernels.length == 1)
        checkboxes.prop('disabled', true);

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

    // Select and show first kernel
    selectKernel(kernels.first().data('kernel-id'));
});
