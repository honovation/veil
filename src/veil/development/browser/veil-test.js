var veil = veil || {};

veil.stopTest = function () {
    $.post('/-test/stop');
};
veil.failTest = function (message) {
    $.post('/-test/fail', {message:message});
    throw new Error(message);
};
veil.assertEqual = function (expected, actual) {
    if (expected != actual) {
        veil.failTest('expected: ' + expected + ', actual: ' + actual);
    }
};
veil.waitUntil = function(condition, onCondition, timeout) {
    timeout = timeout || 1000;
    var elapsed = 0;
    var intervalId = setInterval(function(){
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