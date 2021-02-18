function openStory() {
    const emailStory = $('#email-story')
    emailStory.removeClass('d-none');
    emailStory.addClass('d-flex');
}

function closeStory() {
    const emailStory = $('#email-story')
    emailStory.addClass('d-none');
    emailStory.removeClass('d-flex');
}

function openMenu() {
    $('.delete-patient').removeClass('d-none');
}

function closeMenu() {
    $('.delete-patient').addClass('d-none')
}

$('document').ready(function() {
    baguetteBox.run('.patient-images')
})