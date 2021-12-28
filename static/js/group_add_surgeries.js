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