function openImages() {
    $('.images-container').removeClass('invisible');
}

function closeImages() {
    $('.images-container').addClass('invisible');
}

function openMenu() {
    $('.delete-patient').removeClass('d-none');
}

function closeMenu() {
    $('.delete-patient').addClass('d-none')
}

$(document).ready(function () {
    $('#carousel-1').carousel('pause');
})