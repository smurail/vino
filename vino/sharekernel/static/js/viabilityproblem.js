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
            row = cb.closest('tr');

        // Update visualization
        currentKernel.val(row.data('kernel-id'));

        // Colorize selected row
        row.toggleClass('table-primary', cb.prop('checked'));

        // Unselect all rows but selected row
        checkboxes.not(this).prop('checked', false)
            .closest('tr').removeClass('table-primary');

        // Trigger change event with DOM style because its visualize way
        currentKernel[0].dispatchEvent(new Event('change'));
    });

    // Select and show first kernel
    selectKernel(kernels.first().data('kernel-id'));
});
