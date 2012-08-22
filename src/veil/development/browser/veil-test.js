window.onerror = function (message, url, lineNumber) {
    $.post('/-test/fail', {message:message + ', url: ' + url + ', line#: ' + lineNumber});
    return false;
};
veil.log = function (message) {
    $.post('/-test/log', {message:message});
};
veil.stopTest = function () {
    $.post('/-test/stop');
};
veil.failTest = function (message) {
    throw new Error(message);
};
veil.assertEqual = function (expected, actual) {
    var expectedVal = expected;
    if ($.isFunction(expected)) {
        expectedVal = expected();
    }
    var actualVal = actual;
    if ($.isFunction(actual)) {
        actualVal = actual();
    }
    if (expectedVal != actualVal) {
        veil.failTest('expected: ' + expectedVal + ', actual: ' + actualVal + ', ' + expected + ' != ' + actual);
    }
};
veil.waitUntil = function (condition, onCondition, timeout) {
    timeout = timeout || 1000;
    onCondition = onCondition || veil.stopTest
    var elapsed = 0;
    var intervalId = setInterval(function () {
        elapsed += 500;
        if (condition()) {
            clearInterval(intervalId);
            onCondition();
        } else {
            if (elapsed >= timeout) {
                veil.failTest(condition + ' did not come true in ' + timeout + ' millisecond')
            }
        }
    }, 500);
};
veil.dump = function (element) {
    element = element || $('body');
    veil.log(element.html());
};