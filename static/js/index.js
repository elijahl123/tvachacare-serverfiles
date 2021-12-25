$(document).ready(function () {
    $('.search-patients').on('keyup', function () {
        let information = $(this).val().toLowerCase();
        const query = $('.patient-row')
        query.filter(function () {
            $(this).parent().toggle($(this).text().toLowerCase().indexOf(information) > -1)
        })
        query.find('.include-in-search > span, .include-in-search > a').each(function (i, obj) {
            let page = $(this);
            let pageText = page.text().replace("<span>", "").replace("</span>");
            let theRegEx = new RegExp("(" + information + ")", "i");
            let newHtml = pageText.replace(theRegEx, "<span class='highlight'>$1</span>");
            page.html(newHtml);
        })
    });

});

function profileImage(event) {
    let image = URL.createObjectURL(event.target.files[0]);
    $('.profile-image').attr('src', image)
    console.log(image)
}

$(document).ready(function () {
    $('.btn-surgeries').text("View Denied Surgeries");
    $('.btn-surgeries-approved').text("View Approved Surgeries")
})

function openDeniedSurgeries() {
    if ($('.btn-surgeries').text() === "View Denied Surgeries") {
        $('.denied-patients').slideDown(300, 'swing')
        $('.btn-surgeries').text("Close");
    } else {
        $('.btn-surgeries').text("View Denied Surgeries");
        $('.denied-patients').slideUp(300, 'swing')
    }
}

function openApprovedSurgeries() {
    if ($('.btn-surgeries-approved').text() === "View Approved Surgeries") {
        $('.approved-patients').slideDown(300)
        $('.btn-surgeries-approved').text("Close");
    } else {
        $('.btn-surgeries-approved').text("View Approved Surgeries");
        $('.approved-patients').slideUp(300)
    }
}

function openInfo(patientid) {
    let patientID = '.patient-' + patientid
    if ($(patientID).css('display') !== 'block') {
        $('.patient-list:nth-last-child(2)').css({
            'border-bottom-left-radius': '0',
            'border-bottom-right-radius': '0'
        })
    } else {
        $('.patient-list:nth-last-child(2)').css({
            'border-bottom-left-radius': '8px',
            'border-bottom-right-radius': '8px'
        })
    }
    console.log($(patientID).css('display'))

    $(patientID).slideToggle(300);
}

function openSurgeryInfo(surgeryid) {
    let surgeryID = '.surgery-' + surgeryid
    if ($(surgeryID).css('display') !== 'block') {
        $('.patient-list:nth-last-child(2)').css({
            'border-bottom-left-radius': '0',
            'border-bottom-right-radius': '0'
        })
    } else {
        $('.patient-list:nth-last-child(2)').css({
            'border-bottom-left-radius': '8px',
            'border-bottom-right-radius': '8px'
        })
    }
    console.log($(surgeryID).css('display'))
    $(surgeryID).slideToggle(300);
}

function toggleDeletePatient(id) {
    const container = $('.delete-patient-' + id)
    if (container.css('display') === 'none') {
        container.css('display', 'flex').hide().fadeIn(100);
    } else {
        container.fadeOut(100);
    }
}