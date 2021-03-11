$(document).ready(function () {
    $('.search-patients').on('keyup', function () {
        let information = $(this).val().toLowerCase();
        const query = $('.surgery-list')
        query.filter(function () {
            $(this).toggle($(this).text().toLowerCase().indexOf(information) > -1)
        })
        query.find('a, label').each(function () {
            let page = $(this);
            let pageText = page.text().replace("<span>", "").replace("</span>");
            let theRegEx = new RegExp("(" + information + ")", "i");
            let newHtml = pageText.replace(theRegEx, "<span class='highlight'>$1</span>");
            page.html(newHtml);
        })
    });

});