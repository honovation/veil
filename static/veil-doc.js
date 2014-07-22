jQuery.ajaxSetup({
    async: false
});

var veil = veil || {};

veil.doc = {};

veil.doc.currentPage = null;

veil.doc.setCurrentPage = function (pageName, statementExecutors) {
    veil.doc.currentPage = statementExecutors || {};
    veil.doc.currentPage.pageName = pageName;
};

veil.doc.jsErrors = [];

window.onerror = function(errorMessage) {
    veil.doc.jsErrors.push(errorMessage);
};