$(function() {
    var kernels = $('#kernels tr[data-kernel-id]'),
        checkboxes = $('#kernels input[type=checkbox]'),
        currentKernel = $('.vz-container input[name=kernel]');

    // Attach change event to each kernel checkbox
    checkboxes.on('change', function() {
        var cb = $(this),
            row = cb.closest('tr');

        // Update visualization
        currentKernel.val(row.data('kernel-id'));

        // Trigger change event with DOM style because its visualize way
        currentKernel[0].dispatchEvent(new Event('change'));

        // Colorize selected row
        row.toggleClass('table-primary', cb.prop('checked'));

        // Unselect all rows but selected row
        checkboxes.not(this).prop('checked', false)
            .closest('tr').removeClass('table-primary');
    });

    // Select and show first kernel
    kernels.each(function() {
        var row = $(this),
            kernelId = row.data('kernel-id'),
            disabled = false;

        if (kernelId) {
            // If there is only one kernel, disable the checkbox
            if (kernels.length == 1)
                disabled = true;

            // Check the checkbox and triggers change event to visualize it
            $('#select-kernel-' + kernelId)
                .prop('checked', true)
                .prop('disabled', disabled)
                .trigger('change');

            // That's all Folks
            return false;
        }
    });
});
