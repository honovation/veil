$.ajaxSetup({headers:{'X-XSRF':$.cookie('_xsrf')}});

var veil = veil || {};

veil.log = console.log;

executed = [];
veil.executeOnce = function(hash, func) {
    if ($.inArray(hash, executed) != -1) {
        return
    }
    executed.push(hash);
    func();
};

veil.event = {};

veil.event.subscribe = function (eventName, handler) {
    $(document).bind(eventName, handler);
};

veil.event.publish = function (eventName, args) {
    $(document).trigger(eventName, args);

    if (veil.event.hasDelegation(eventName)) {
        $(veil.event.DELEGATIONS[eventName]).each(function () {
            veil.event.publish(this, args);
        });
    }
};

veil.event.DELEGATIONS = {};

veil.event.delegate = function (srcEventName, destEventName) {
// TODO: check endless loop of delegation
    if (!veil.event.hasDelegation(srcEventName)) {
        veil.event.DELEGATIONS[srcEventName] = [];
    }
    veil.event.DELEGATIONS[srcEventName].push(destEventName);
};

veil.event.hasDelegation = function (srcEventName) {
    return veil.event.DELEGATIONS[srcEventName];
};

veil.showMessage = function (message) {
    alert(message);
};

veil.resource = {};

veil.resource.get = function (options) {
    var url = options.url;
    var onSuccess = options.onSuccess;
    var onValidationError = options.onValidationError;
    var dataType = options.dataType;
    var _ = {
        type:'GET',
        url:url,
        dataType:dataType,
        success:onSuccess,
        statusCode:{
            400:onValidationError
        }
    };
    $.ajax(_);
};

veil.resource.create = function (options) {
    var url = options.url;
    var data = options.data;
    var onSuccess = options.onSuccess;
    var onError = options.onError;
    var onValidationError = options.onValidationError;
    var dataType = options.dataType;
    var _ = {
        type:'POST',
        url:url,
        data:data,
        dataType:dataType,
        success:onSuccess,
        error:onError,
        statusCode:{
            400:onValidationError
        }
    };
    $.ajax(_);
};

veil.resource.update = function (options) {
    var url = options.url;
    var data = options.data;
    var onSuccess = options.onSuccess;
    var onError = options.onError;
    var onValidationError = options.onValidationError;
    var _ = {
        type:'PUT',
        url:url,
        data:data,
        success:onSuccess,
        error:onError,
        statusCode:{
            400:onValidationError
        }
    };
    $.ajax(_);
};

veil.resource.del = function (options) {
    var url = options.url;
    var onSuccess = options.onSuccess;
    var _ = {
        type:'DELETE',
        url:url,
        success:onSuccess
    };
    $.ajax(_);
};

veil.widget = {};

veil.widget.handle = function (widget_selector, child_selector, event, handler) {
    $(widget_selector + ' ' + child_selector).live(event, function (e) {
        var widget = $(this).parents(widget_selector);
        return handler(widget, e);
    });
};

veil.widget.delResource = function (widget, onSuccess) {
    var _ = {
        url:widget.data('delete-url'),
        onSuccess:function () {
            widget.remove();
            onSuccess();
        }
    };
    veil.resource.del(_);
};

veil.widget.createResource = function (widget, onSuccess, dataType) {
    veil.widget.clearErrorMessages(widget);
    var _ = {
        url:widget.attr('action'),
        data:widget.serialize(),
        dataType: dataType,
        onSuccess:function (s) {
            widget[0].reset();
            onSuccess(s);
        },
        onError:function () {
            veil.widget.showErrorMessage(widget, '操作失败');
        },
        onValidationError:function (xhr) {
            var new_widget = $(veil.widget.processWidget(xhr.responseText));
            widget.replaceWith(new_widget);
            widget = new_widget;
            veil.widget.showErrorMessage(widget, '提交的信息未被服务器接受');
            veil.widget.showFieldErrorMessage(widget);
        }
    };
    veil.resource.create(_);
};

veil.widget.updateResource = function (widget, onSuccess) {
    veil.widget.clearErrorMessages(widget);
    var _ = {
        url:widget.attr('action'),
        data:widget.serialize(),
        onSuccess:function () {
            widget[0].reset();
            onSuccess();
        },
        onError:function () {
            veil.widget.showErrorMessage(widget, '操作失败');
        },
        onValidationError:function (xhr) {
            var new_widget = $(veil.widget.processWidget(xhr.responseText));
            widget.replaceWith(new_widget);
            widget = new_widget;
            veil.widget.showErrorMessage(widget, '提交的信息未被服务器接受');
            veil.widget.showFieldErrorMessage(widget);
        }
    };
    veil.resource.update(_);
};

veil.widget.showErrorMessage = function(widget, defaultErrorMessage) {
    var errorMessage = widget.data('error-message') || defaultErrorMessage;
    widget.prepend(
        '<span class="error-message label label-warning">' +
            '<i class="icon-info-sign"></i>' +
            errorMessage + '</span>');
};

veil.widget.showFieldErrorMessage = function(widget) {
    var allErrors = widget.data('errors');
    for (var field in allErrors) {
        if (allErrors.hasOwnProperty(field)) {
            var errors = $(allErrors[field]);
            errors.each(function () {
                var error = this;
                $('<span class="error-message label label-warning"><i class="icon-info-sign"></i>'
                      + error + '</span>').insertBefore(
                    widget.find('[name=' + field + ']')
                );
            });
        }
    }
};

veil.widget.clearErrorMessages = function(widget) {
    widget.find('.error-message').remove();
};

veil.widget.refresh = function (widget) {
    veil.resource.get({
        url: widget.data('refreshUrl'),
        onSuccess: function (html) {
            html = veil.widget.processWidget(html);
            widget.replaceWith(html);
        }
    });
};
veil.widget.loadedJavascripts = [];
veil.widget.loadedStylesheets = [];
veil.widget.RE_SCRIPT = /<script.*?><\/script>/ig;
veil.widget.RE_LINK = /<link.*?\/?>(<\/link>)?/ig;
veil.widget.processWidget = function(html) {
    function loadJavascript(url) {
        if ($('body').html().indexOf(url) == -1) {
            if ($.inArray(url, veil.resource.loadedJavascripts) == -1) {
                veil.widget.loadedJavascripts.push(url);
                var script = document.createElement('script');
                script.type = 'text/javascript';
                script.src = url;
                $('body').append(script);
            }
        }
    }
    function loadStylesheet(url) {
        if ($('body').html().indexOf(url) == -1) {
            if ($.inArray(url, veil.resource.loadedStylesheets) == -1) {
                veil.widget.loadedStylesheets.push(url);
                var link = document.createElement('link');
                link.rel = 'stylesheet';
                link.type = 'text/css';
                link.href = url;
                $('body').append(link);
            }
        }
    }
    html = html.replace(veil.widget.RE_SCRIPT, function(scriptElement) {
        loadJavascript($(scriptElement).attr('src'));
        return '';
    });
    html = html.replace(veil.widget.RE_LINK, function(linkElement) {
        var $linkElement = $(linkElement);
        if ('stylesheet' != $linkElement.attr('rel')) {
            return linkElement;
        }
        var url = $linkElement.attr('href');
        if (url) {
            loadStylesheet(url);
            return '';
        } else {
            return linkElement;
        }
    });
    return html;
};
