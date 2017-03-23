;
/*!
 * veil.js
 *
 * @requires jQuery v1.8+
 * @requires Javascript Cookie (https://github.com/js-cookie/js-cookie) latest
 * @optional json3.js(https://github.com/bestiejs/json3) for browsers without native JSON support
 *
 */

$.ajaxSetup({cache: true, headers: {'X-XSRF': Cookies.get('_xsrf')}});

$(document).on('click', 'button,input[type="button"],input[type="submit"]', function (e) {
    var $this = $(this);
    if($this.data('ignoreDoubleClick')) {
        e.preventDefault();
        e.stopPropagation();
    } else {
        $this.addClass('disabled');
        $this.data('ignoreDoubleClick', setTimeout(function () {
            $this.removeClass('disabled');
            $this.data('ignoreDoubleClick', null);
        }, 500));
    }
});

$.fn.serializeObject = function() {
    var o = {value_contained_in_array: true};
    var a = this.serializeArray();
    $.each(a, function() {
        var value = $.trim(this.value);
        if (value) {
            if (o[this.name] === undefined) {
                o[this.name] = [value];
            } else {
                o[this.name].push(value);
            }
        }
    });
    return o;
};

var veil = veil || {};

veil.defaultAuthenticationErrorHandler = function(jqXHR) {
    var loginUrl = jqXHR.getResponseHeader('WWW-Authenticate');
    if (window.location.pathname === loginUrl) {
        $('form input[type=text],[type=email],[type=number],[type=tel]').filter(':enabled:visible:not([readonly]):first').focus().select();
    } else {
        window.location.href = loginUrl + encodeURIComponent(window.location.hash);
    }
};

veil.defaultForbiddenErrorHandler = function() {veil.alert('权限不足');};

veil.log = function(message) {
    if ("undefined" !== typeof console) {
        console.log(message);
    }
};

veil.alert = function(message){(window.custom_alert || window.alert)(message);};

veil.executed = [];
veil.executeOnce = function (hash, func) {
    if ($.inArray(hash, veil.executed) != -1) {
        return;
    }
    veil.executed.push(hash);
    func();
};

veil.event = {};

veil.event.reset = function () {
    $.each(veil.event.SUBSCRIBERS, function (eventName, handlers) {
        $.each(handlers, function () {
            $(document).off(eventName, this);
        });
    });

    veil.event.SUBSCRIBERS = {};
    veil.event.DELEGATIONS = {};
};

veil.event.SUBSCRIBERS = {};

veil.event.subscribe = function (eventName, handler) {
    if (veil.event.SUBSCRIBERS[eventName]) {
        if ($.inArray(handler, veil.event.SUBSCRIBERS[eventName]) != -1) {
            return;
        }
    } else {
        veil.event.SUBSCRIBERS[eventName] = [];
    }
    veil.event.SUBSCRIBERS[eventName].push(handler);
    $(document).on(eventName, handler);
};

veil.event.unsubscribe = function (eventName, handler) {
    if (veil.event.SUBSCRIBERS[eventName]) {
        var index = $.inArray(handler, veil.event.SUBSCRIBERS[eventName]);
        if ( index != -1) {
            veil.event.SUBSCRIBERS[eventName].splice(index, 1);
        }
    }
    $(document).off(eventName, handler);
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
    if (veil.event.hasDelegation(srcEventName) && $.inArray(destEventName, veil.event.DELEGATIONS[srcEventName]) != -1) {
        return;
    }
    if (veil.event.hasDelegationLoop(srcEventName, destEventName)) {
        veil.log('cannot delegate event ' + srcEventName + ' to ' + destEventName+ ': cause endless delegation loop');
        return;
    }
    if (!veil.event.hasDelegation(srcEventName)) {
        veil.event.DELEGATIONS[srcEventName] = [];
    }
    veil.event.DELEGATIONS[srcEventName].push(destEventName);
};

veil.event.hasDelegation = function (srcEventName) {
    return veil.event.DELEGATIONS[srcEventName];
};

veil.event.hasDelegationLoop = function (srcEventName, destEventName) {
    if (!veil.event.hasDelegation(destEventName)) {
        return false;
    }
    if ($.inArray(srcEventName, veil.event.DELEGATIONS[destEventName]) != -1) {
        return true;
    }
    for (var i = 0, len = veil.event.DELEGATIONS[destEventName].length; i < len; i++) {
        if (veil.event.hasDelegationLoop(srcEventName, veil.event.DELEGATIONS[destEventName][i])) {
           return true;
        }
    }
    return false;
};

veil.resource = {};

veil.resource.get = function (options) {
    var url = options.url;
    var async = options.async;
    var cache = options.cache;
    if (cache !== false && url.indexOf('_v_ajax=1') === -1) {
        url += (url.indexOf('?') === -1 ? '?' : '&') + '_v_ajax=1';
    }
    var onSuccess = options.onSuccess;
    var onError = options.onError;
    var onValidationError = options.onValidationError;
    var onAuthenticationError = options.onAuthenticationError || veil.defaultAuthenticationErrorHandler;
    var dataType = options.dataType;
    var data = options.data;
    var widget = options.widget;
    if (widget){
        veil.widget.clearErrorMessages(widget);
        onSuccess = function (html) {
            if (options.onSuccess){
                veil.widget.processWidget(html, options.onSuccess);
            }
        };
        if (!onError){
            onError = function (xhr) {
                if (xhr.status != 400 && xhr.status != 401 && xhr.status != 403) {
                    veil.widget.showErrorMessage(widget, {'@': '操作失败'});
                }
            };
        }
        if (!onValidationError){
            onValidationError = function (xhr) {
                veil.widget.showErrorMessage(widget, $.parseJSON(xhr.responseText));
            };
        }
    }
    var _ = {
        type: 'GET',
        url: url,
        async: async,
        cache: cache,
        data: data,
        dataType: dataType,
        success: onSuccess,
        error: onError,
        statusCode: {
            400: onValidationError,
            401: onAuthenticationError,
            403: function() {veil.alert('权限不足');},
            500: function() {veil.alert('服务内部错误');},
            502: function() {veil.alert('服务暂时不可用，请稍后重试');},
            503: function() {veil.alert('服务暂时不可用，请稍后重试');}
        }
    };
    return $.ajax(_);
};

veil.resource.create = function (options) {
    var url = options.url;
    var async = options.async;
    var data = options.data;
    var dataFormat = options.dataFormat;
    var dataType = options.dataType;
    var onSuccess = options.onSuccess;
    var onError = options.onError;
    var onValidationError = options.onValidationError;
    var onAuthenticationError = options.onAuthenticationError || veil.defaultAuthenticationErrorHandler;
    var onForbiddenError = options.onForbiddenError || veil.defaultForbiddenErrorHandler;
    var onComplete = options.onComplete;
    var widget = options.widget;
    if (widget){
        veil.widget.clearErrorMessages(widget);
        if (!onError){
            onError = function (xhr) {
                if (xhr.status != 400 && xhr.status != 401 && xhr.status != 403) {
                    veil.widget.showErrorMessage(widget, {'@': '操作失败'});
                }
            };
        }
        if (!onValidationError){
            onValidationError = function (xhr) {
                veil.widget.showErrorMessage(widget, $.parseJSON(xhr.responseText));
            };
        }
    }
    var _ = {
        type:'POST',
        url:url,
        async:async,
        data:data,
        dataType:dataType,
        success:onSuccess,
        error:onError,
        complete:onComplete,
        statusCode:{
            400: onValidationError,
            401: onAuthenticationError,
            403: onForbiddenError,
            404: function() {veil.alert('未找到')},
            500: function() {veil.alert('服务内部错误');},
            502: function() {veil.alert('服务暂时不可用，请稍后重试');},
            503: function() {veil.alert('服务暂时不可用，请稍后重试');}
        }
    };
    if(dataFormat === 'json') {
        _.data = JSON.stringify(_.data || {});
        _.contentType = 'application/json; charset=utf-8';
    }
    return $.ajax(_);
};

veil.resource.update = function (options) {
    var url = options.url;
    var data = options.data;
    var dataFormat = options.dataFormat;
    var dataType = options.dataType;
    var onSuccess = options.onSuccess;
    var onError = options.onError;
    var onValidationError = options.onValidationError;
    var onAuthenticationError = options.onAuthenticationError || veil.defaultAuthenticationErrorHandler;
    var widget = options.widget;
    if (widget){
        veil.widget.clearErrorMessages(widget);
        if (!onError){
            onError = function (xhr) {
                if (xhr.status != 400 && xhr.status != 401 && xhr.status != 403) {
                    veil.widget.showErrorMessage(widget, {'@': '操作失败'});
                }
            };
        }
        if (!onValidationError){
            onValidationError = function (xhr) {
                veil.widget.showErrorMessage(widget, $.parseJSON(xhr.responseText));
            };
        }
    }
    var _ = {
        type: 'PUT',
        url: url,
        data: data,
        dataType:dataType,
        success: onSuccess,
        error: onError,
        statusCode: {
            400: onValidationError,
            401: onAuthenticationError,
            403: function() {veil.alert('权限不足');},
            404: function() {veil.alert('未找到')},
            500: function() {veil.alert('服务内部错误');},
            502: function() {veil.alert('服务暂时不可用，请稍后重试');},
            503: function() {veil.alert('服务暂时不可用，请稍后重试');}
        }
    };

    // TODO: remove this code after 2017.08.01
    var qqBrowser = navigator.appVersion.match(/\sMQQBrowser\/\d\.*\d/);
    if (qqBrowser) {
        if (parseFloat(qqBrowser[0].split('/')[1]) < 5.8) {
            $.extend(_, {type: 'POST'});
            _.data._method = 'PUT';
        }
    }

    if(dataFormat === 'json') {
        _.data = JSON.stringify(_.data || {});
        _.contentType = 'application/json; charset=utf-8';
    }
    return $.ajax(_);
};

veil.resource.patch = function (options) {
    var url = options.url;
    var data = options.data;
    var dataFormat = options.dataFormat;
    var dataType = options.dataType;
    var onSuccess = options.onSuccess;
    var onError = options.onError;
    var onValidationError = options.onValidationError;
    var onAuthenticationError = options.onAuthenticationError || veil.defaultAuthenticationErrorHandler;
    var widget = options.widget;
    if (widget){
        veil.widget.clearErrorMessages(widget);
        if (!onError){
            onError = function (xhr) {
                if (xhr.status != 400 && xhr.status != 401 && xhr.status != 403) {
                    veil.widget.showErrorMessage(widget, {'@': '操作失败'});
                }
            };
        }
        if (!onValidationError){
            onValidationError = function (xhr) {
                veil.widget.showErrorMessage(widget, $.parseJSON(xhr.responseText));
            };
        }
    }
    var _ = {
        type: 'PATCH',
        url: url,
        data: data,
        dataType: dataType,
        success: onSuccess,
        error: onError,
        statusCode: {
            400: onValidationError,
            401: onAuthenticationError,
            403: function() {veil.alert('权限不足');},
            404: function() {veil.alert('未找到')},
            500: function() {veil.alert('服务内部错误');},
            502: function() {veil.alert('服务暂时不可用，请稍后重试');},
            503: function() {veil.alert('服务暂时不可用，请稍后重试');}
        }
    };

    // TODO: remove this code after 2017.08.01
    var qqBrowser = navigator.appVersion.match(/\sMQQBrowser\/\d\.*\d/);
    if (qqBrowser) {
        if (parseFloat(qqBrowser[0].split('/')[1]) < 5.8) {
            $.extend(_, {type: 'POST'});
            _.data._method = 'PATCH';
        }
    }

    if (dataFormat === 'json') {
        _.data = JSON.stringify(_.data || {});
        _.contentType = 'application/json; charset=utf-8';
    }
    return $.ajax(_);
};

veil.resource.del = function (options) {
    var url = options.url;
    var data = options.data;
    var dataType = options.dataType;
    var onSuccess = options.onSuccess;
    var onError = options.onError;
    var onValidationError = options.onValidationError;
    var onAuthenticationError = options.onAuthenticationError || veil.defaultAuthenticationErrorHandler;
    var widget = options.widget;
    if (widget){
        var widgetParent = widget.parent();
        veil.widget.clearErrorMessages(widget);
        onSuccess = function () {
            widget.remove();
            widgetParent.append('正在删除...');
            if (options.onSuccess){
                options.onSuccess();
            }
        };
        if (!onError){
            onError = function (xhr) {
                if (xhr.status != 400 && xhr.status != 401 && xhr.status != 403) {
                    veil.widget.showErrorMessage(widget, {'@': '操作失败'});
                }
            };
        }
        if (!onValidationError){
            onValidationError = function (xhr) {
                veil.widget.showErrorMessage(widget, $.parseJSON(xhr.responseText));
            };
        }
    }
    var _ = {
        type:'DELETE',
        url:url,
        data: data,
        dataType: dataType,
        success:onSuccess,
        error:onError,
        statusCode:{
            400: onValidationError,
            401: onAuthenticationError,
            403: function() {veil.alert('权限不足');},
            404: function() {veil.alert('未找到')},
            500: function() {veil.alert('服务内部错误');},
            502: function() {veil.alert('服务暂时不可用，请稍后重试');},
            503: function() {veil.alert('服务暂时不可用，请稍后重试');}

        }
    };
    return $.ajax(_);
};

veil.alertErrorMessage = function (allErrors, displayAll) {
    var errors = [];
    for (var field in allErrors) {
        if (allErrors.hasOwnProperty(field)) {
            if (displayAll) {
                errors.push(field + ': ' + allErrors[field]);
            } else {
                errors.push(allErrors[field]);
                break;
            }
        }
    }
    veil.alert(errors.join('\n'));
};

veil.widget = {};

veil.widget.reset = function () {
    $.each(veil.widget.HANDLERS, function (event, selectors) {
        $.each(selectors, function (index, selector) {
            $(document).off(event, selector);
        });
    });

    veil.widget.HANDLERS = {};

    if (veil.widget.loadedJavascripts.length) {
        $('script').each(function(){
            if (veil.widget.loadedJavascripts.indexOf($(this).attr('src')) !== -1) {
                $(this).remove();
            }
        });
        veil.widget.loadedJavascripts = [];
    }

    if (veil.widget.loadedStylesheets.length) {
        $('link[rel=stylesheet]').each(function(){
            if (veil.widget.loadedStylesheets.indexOf($(this).attr('href')) !== -1) {
                $(this).remove();
            }
        });
        veil.widget.loadedStylesheets = [];
    }

    veil.widget.initializers = [];
};

veil.widget.HANDLERS = {};

veil.widget.handle = function (widget_selector, child_selector, event, handler, base_selector) {
    var selector = widget_selector && child_selector ? widget_selector + ' ' + child_selector : widget_selector || child_selector;
    var fullSelector = base_selector ? base_selector + ' ' + selector : selector;
    if (veil.widget.HANDLERS[event]) {
        if ($.inArray(fullSelector, veil.widget.HANDLERS[event]) != -1) {
            return;
        }
    } else {
        veil.widget.HANDLERS[event] = [];
    }
    veil.widget.HANDLERS[event].push(fullSelector);

    $(base_selector || document).on(event, selector, function () {
        var widget = widget_selector && child_selector ? $(this).parents(widget_selector) : $(this);
        veil.widget.clearErrorMessages(widget);
        var newArgs = [widget];
        for (var i = 0; i < arguments.length; i++) {
            newArgs.push(arguments[i]);
        }
        return handler.apply(this, newArgs);
    });
};

veil.widget.createResource = function (widget, onSuccess, data, dataFormat, dataType, onComplete) {
    if (data === undefined) {
        data = dataFormat === 'json' ? widget.serializeObject() : widget.serialize();
    }
    var _ = {
        widget: widget,
        url: widget.attr('action') || widget.data('action'),
        data: data,
        dataFormat: dataFormat,
        dataType: dataType,
        onSuccess: onSuccess,
        onComplete: onComplete
    };
    return veil.resource.create(_);
};

veil.widget.updateResource = function (widget, onSuccess, data, dataFormat, dataType) {
    if (data === undefined) {
        data = dataFormat === 'json' ? widget.serializeObject() : widget.serialize();
    }
    var _ = {
        widget: widget,
        url: widget.attr('action') || widget.data('action'),
        data: data || widget.serialize(),
        dataFormat: dataFormat,
        dataType: dataType,
        onSuccess: onSuccess
    };
    return veil.resource.update(_);
};

veil.widget.patchResource = function(widget, onSuccess, data, dataFormat, dataType) {
    if (data === undefined) {
        data = dataFormat === 'json' ? widget.serializeObject() : widget.serialize();
    }
    var _ = {
        widget: widget,
        url: widget.attr('action') || widget.data('action'),
        data: data || widget.serialize(),
        dataFormat: dataFormat,
        dataType: dataType,
        onSuccess: onSuccess
    };
    return veil.resource.patch(_);
};

veil.widget.getResource = function (widget, onSuccess) {
    var _ = {
        widget: widget,
        url: widget.attr('action') || widget.data('action'),
        data: widget.serialize(),
        onSuccess: onSuccess
    };
    return veil.resource.get(_);
};

veil.widget.delResource = function (widget, onSuccess) {
    var _ = {
        widget: widget,
        url: widget.data('deleteUrl'),
        onSuccess: onSuccess
    };
    return veil.resource.del(_);
};

veil.widget.get = function (url, onSuccess, data) {
    return veil.resource.get({
        url: url,
        data: data,
        onSuccess: function (html) {
            veil.widget.processWidget(html, onSuccess);
        }
    });
};

veil.widget.refresh = function (widget, options) {
    options = options || {};
    var refreshUrl = options.refreshUrl || widget.data('refreshUrl');
    var data=options.data;
    var onSuccess = options.onSuccess;
    if (refreshUrl) {
        veil.resource.get({
            widget: widget,
            url: refreshUrl,
            data: data,
            onSuccess: function (html) {
                var token = 'refreshed-' + Math.round(Math.random()*1000);
                widget.replaceWith($(html).attr('data-refresh-token', token));
                var refreshedWidget = $('[data-refresh-token=' + token + ']');
                if (refreshedWidget.length) {
                    if (onSuccess) {
                        onSuccess(refreshedWidget);
                    }
                } else {
                    veil.log('widget disappeared after refreshed from: ' + refreshUrl);
                }
            }
        });
    } else {
        veil.log('missing refreshUrl');
    }
};

veil.widget.showErrorMessage = function (widget, allErrors) {
    for (var field in allErrors) {
        if (allErrors.hasOwnProperty(field)) {
            var error = allErrors[field];
            if (field === '@') {
                widget.prepend('<span class="error-message label label-warning summary-error-message"><i class="icon-info-sign"></i>' + error + '</span>');
            } else {
                var $field = widget.find('[name=' + field + ']:first');
                if ($field.length) {
                    var $error = $('<span class="error-message label label-warning"><i class="icon-info-sign"></i>' + error + '</span>');
                    if ($field.parent().hasClass('input-group')) {
                        $error.insertAfter($field.parent());
                    } else {
                        $error.insertAfter($field);
                    }
                } else {
                    widget.prepend('<span class="error-message label label-warning summary-error-message"><i class="icon-info-sign"></i>' + error + '</span>');
                }
            }
        }
    }
};

veil.widget.clearErrorMessages = function (widget) {
    widget.find('.error-message').remove();
};

veil.widget.loadedJavascripts = [];
veil.widget.loadedStylesheets = [];
veil.widget.RE_SCRIPT = /<script.*?><\/script>/ig;
veil.widget.RE_LINK = /<link.*?\/?>(<\/link>)?/ig;
veil.widget.initializers = [];
veil.widget.processWidget = function (html, processHtml) {
    var $body;
    var bodyHtml;
    function loadJavascript(url) {
        if ($.inArray(url, veil.widget.loadedJavascripts) == -1) {
            veil.widget.loadedJavascripts.push(url);
            if (!$body) {
                $body = $('body');
                bodyHtml = $body.html();
            }
            if (bodyHtml.indexOf(url) == -1) {
                var script = document.createElement('script');
                script.type = 'text/javascript';
                script.src = url;
                $body.append(script);
            }
        }
    }
    function loadStylesheet(url) {
        if ($.inArray(url, veil.widget.loadedStylesheets) == -1) {
            veil.widget.loadedStylesheets.push(url);
            if (!$body) {
                $body = $('body');
                bodyHtml = $body.html();
            }
            if (bodyHtml.indexOf(url) == -1) {
                var link;
                if(document.createStyleSheet) {
                    link = document.createStyleSheet(url);
                } else {
                    link = document.createElement('link');
                    link.rel = 'stylesheet';
                    link.type = 'text/css';
                    link.href = url;
                }
                $body.append(link);
            }
        }
    }
    var javascriptUrls = [];
    html = html.replace(veil.widget.RE_SCRIPT, function (scriptElement) {
        javascriptUrls.push($(scriptElement).attr('src'));
        return '';
    });
    var stylesheetUrls = [];
    html = html.replace(veil.widget.RE_LINK, function (linkElement) {
        var $linkElement = $(linkElement);
        if ('stylesheet' != $linkElement.attr('rel')) {
            return linkElement;
        }
        var url = $linkElement.attr('href');
        if (url) {
            stylesheetUrls.push(url);
            return '';
        } else {
            return linkElement;
        }
    });
    $(stylesheetUrls).each(function() {
        loadStylesheet(String(this));
    });
    processHtml(html);
    $(javascriptUrls).each(function() {
        loadJavascript(String(this));
    });
    $(veil.widget.initializers).each(function() {
        this();
    });
};

veil.reset = function() {
    veil.executed = [];
    veil.event.reset();
    veil.widget.reset();
};
