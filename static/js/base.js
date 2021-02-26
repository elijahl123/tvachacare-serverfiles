window.dataLayer = window.dataLayer || [];

function gtag() {
    dataLayer.push(arguments);
}

gtag('js', new Date());

gtag('config', 'UA-172938628-2');


function hours12(date) {
    return (date.getUTCHours() + 16) % 12 || 12;
}

function formatAMPM(hours) {
    if (hours >= 24) {
        hours -= 24
    }
    return hours >= 12 ? 'pm' : 'am'
}

function startTime() {
    let today = new Date();
    let h = hours12(today);
    let m = today.getUTCMinutes();
    m = checkTime(m);
    document.getElementById('current_time').innerHTML =
        h + ":" + m + formatAMPM(today.getUTCHours() + 16);
    let t = setTimeout(startTime, 500);
}

function checkTime(i) {
    if (i < 10) {
        i = "0" + i
    }
    // add zero in front of numbers < 10
    return i;
}


function createRipple(event) {
    const button = event.currentTarget;

    const circle = document.createElement("span");
    const diameter = Math.max(button.clientWidth, button.clientHeight);
    const radius = diameter / 2;

    circle.style.width = circle.style.height = `${diameter}px`;
    circle.style.left = `${event.clientX - button.offsetLeft - radius}px`;
    circle.style.top = `${event.clientY - button.offsetTop - radius}px`;
    circle.classList.add("ripple");

    const ripple = button.getElementsByClassName("ripple")[0];

    if (ripple) {
        ripple.remove();
    }

    button.appendChild(circle);

    console.log('hello')
}

$(document).ready(function () {
    const buttons = document.getElementsByClassName('btn-ripple');
    for (const button of buttons) {
        button.addEventListener("click", createRipple);
    }

    $('.toast').toast('show')

})
