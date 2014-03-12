;
/*!
 * veil.js
 *
 * @requires jQuery v1.8+
 * @requires jQuery Cookie Plugin v1.4+
 * @requires json3.js(https://github.com/bestiejs/json3) for browsers without native JSON support
 *
 */

$.ajaxSetup({headers:{'X-XSRF':$.cookie('_xsrf')}});

$.fn.serializeObject = function() {
    var o = {api: false};
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

veil.log = function(message) {
    if ("undefined" !== typeof console) {
        console.log(message);
    }
};

executed = [];
veil.executeOnce = function (hash, func) {
    if ($.inArray(hash, executed) != -1) {
        return;
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
/* TODO: check endless loop of delegation */
    if (!veil.event.hasDelegation(srcEventName)) {
        veil.event.DELEGATIONS[srcEventName] = [];
    }
    veil.event.DELEGATIONS[srcEventName].push(destEventName);
};

veil.event.hasDelegation = function (srcEventName) {
    return veil.event.DELEGATIONS[srcEventName];
};

veil.resource = {};

veil.resource.get = function (options) {
    var url = options.url;
    var onSuccess = options.onSuccess;
    var onError = options.onError;
    var onValidationError = options.onValidationError;
    var dataType = options.dataType;
    var data = options.data;
    var widget = options.widget;
    if (widget){
        veil.widget.clearErrorMessages(widget);
        onSuccess = function (html) {
            if(widget[0].reset){
                widget[0].reset();
            }
            if (options.onSuccess){
                veil.widget.processWidget(html, options.onSuccess);
            }
        };
        if (!onError){
            onError = function (xhr) {
                if (xhr.status != 400 && xhr.status != 401 && xhr.status != 403) {
                    veil.widget.showErrorMessage(widget, {'@':'操作失败'});
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
        cache: false,
        type: 'GET',
        url: url,
        data: data,
        dataType: dataType,
        success: onSuccess,
        error: onError,
        statusCode: {
            400: onValidationError,
            401: function(){
                alert('登录信息不对、或者帐号被禁用');
                if (window.location.pathname === '/login'){
                    $('input[name=username]').focus().select();
                } else {
                    window.location.href = '/login';
                }
            },
            403: function() {alert('权限不足');}
        }
    };
    return $.ajax(_);
};

veil.resource.create = function (options) {
    var url = options.url;
    var data = options.data;
    var dataFormat = options.dataFormat;
    var dataType = options.dataType;
    var async = options.async;
    var onSuccess = options.onSuccess;
    var onError = options.onError;
    var onValidationError = options.onValidationError;
    var widget = options.widget;
    if (widget){
        veil.widget.clearErrorMessages(widget);
        onSuccess = function (s) {
            if(widget[0].reset){
                widget[0].reset();
            }
            if (options.onSuccess){
                options.onSuccess(s);
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
        type:'POST',
        url:url,
        data:data,
        async:async,
        dataType:dataType,
        success:onSuccess,
        error:onError,
        statusCode:{
            400: onValidationError,
            401: function(){
                alert('登录信息不对、或者帐号被禁用');
                if (window.location.pathname === '/login'){
                    $('input[name=username]').focus().select();
                } else {
                    window.location.href = '/login';
                }
            },
            403: function() {alert('权限不足');}
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
    var widget = options.widget;
    if (widget){
        veil.widget.clearErrorMessages(widget);
        onSuccess = function (s) {
            if(widget[0].reset){
                widget[0].reset();
            }
            if (options.onSuccess){
                options.onSuccess(s);
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
        type: 'PUT',
        url: url,
        data: data,
        dataType:dataType,
        success: onSuccess,
        error: onError,
        statusCode: {
            400: onValidationError,
            401: function(){
                alert('登录信息不对、或者帐号被禁用');
                if (window.location.pathname === '/login'){
                    $('input[name=username]').focus().select();
                } else {
                    window.location.href = '/login';
                }
            },
            403: function() {alert('权限不足');}
        }
    };
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
    var widget = options.widget;
    if (widget){
        veil.widget.clearErrorMessages(widget);
        onSuccess = function (s) {
            if(widget[0].reset){
                widget[0].reset();
            }
            if (options.onSuccess){
                options.onSuccess(s);
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
        type: 'PATCH',
        url: url,
        data: data,
        dataType: dataType,
        success: onSuccess,
        error: onError,
        statusCode: {
            400: onValidationError,
            401: function(){
                alert('登录信息不对、或者帐号被禁用');
                if (window.location.pathname === '/login'){
                    $('input[name=username]').focus().select();
                } else {
                    window.location.href = '/login';
                }
            },
            403: function() {alert('权限不足');}
        }
    };
    if(dataFormat === 'json') {
        _.data = JSON.stringify(_.data || {});
        _.contentType = 'application/json; charset=utf-8';
    }
    return $.ajax(_);
};

veil.resource.del = function (options) {
    var url = options.url;
    var onSuccess = options.onSuccess;
    var onError = options.onError;
    var widget = options.widget;
    if (widget){
        veil.widget.clearErrorMessages(widget);
        onSuccess = function () {
            widget.remove();
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
    }
    var _ = {
        type:'DELETE',
        url:url,
        success:onSuccess,
        error:onError,
        statusCode:{
            401: function(){
                alert('登录信息不对、或者帐号被禁用');
                if (window.location.pathname === '/login'){
                    $('input[name=username]').focus().select();
                } else {
                    window.location.href = '/login';
                }
            },
            403:function() {alert('权限不足');}
        }
    };
    return $.ajax(_);
};

veil.widget = {};

veil.widget.handle = function (widget_selector, child_selector, event, handler) {
    $(document).on(event, child_selector ? widget_selector + ' ' + child_selector : widget_selector, function () {
        var widget = child_selector ? $(this).parents(widget_selector) : $(this);
        var newArgs = [widget];
        for(var i = 0; i < arguments.length; i++) {
            newArgs.push(arguments[i]);
        }
        return handler.apply(this, newArgs);
    });
};

veil.widget.createResource = function (widget, onSuccess, data, dataFormat, dataType) {
    if (data === undefined) {
        data = dataFormat === 'json' ? widget.serializeObject() : widget.serialize();
    }
    var _ = {
        widget: widget,
        url: widget.attr('action'),
        data: data,
        dataFormat: dataFormat,
        dataType: dataType,
        onSuccess: onSuccess
    };
    return veil.resource.create(_);
};

veil.widget.updateResource = function (widget, onSuccess, data, dataFormat, dataType) {
    if (data === undefined) {
        data = dataFormat === 'json' ? widget.serializeObject() : widget.serialize();
    }
    var _ = {
        widget: widget,
        url:widget.attr('action'),
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
        url: widget.attr('action'),
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
        url:widget.attr('action'),
        data:widget.serialize(),
        onSuccess:onSuccess
    };
    return veil.resource.get(_);
};

veil.widget.delResource = function (widget, onSuccess) {
    var _ = {
        widget: widget,
        url:widget.data('deleteUrl'),
        onSuccess:onSuccess
    };
    return veil.resource.del(_);
};

veil.widget.get = function (url, onSuccess, data) {
    return veil.resource.get({
        url:url,
        data:data,
        onSuccess:function (html) {
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
            url:refreshUrl,
            data:data,
            onSuccess:function (html) {
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
            var errors = (typeof allErrors[field] === 'string') ? [allErrors[field]] : allErrors[field];
            errors.reverse();
            $(errors).each(function () {
                var error = this;
                if (field === '@'){
                    widget.prepend('<span class="error-message label label-warning summary-error-message"><i class="icon-info-sign"></i>' + error + '</span>');
                } else {
                    var $field = widget.find('[name=' + field + ']');
                    var $error = $('<span class="error-message label label-warning"><i class="icon-info-sign"></i>' + error + '</span>');
                    $error.insertAfter( $field );
                }
            });
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
        loadStylesheet(this);
    });
    processHtml(html);
    $(javascriptUrls).each(function() {
        loadJavascript(this);
    });
    $(veil.widget.initializers).each(function() {
        this();
    });
};
