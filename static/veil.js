/*!
 * veil.js
 *
 * @requires jQuery v1.8+
 * @requires jQuery Cookie Plugin v1.4+
 * @requires json3.js(https://github.com/bestiejs/json3) for browsers born before ECScript5
 *
 */

$.ajaxSetup({headers:{'X-XSRF':$.cookie('_xsrf')}});

$.fn.serializeObject = function() {
    var o = {};
    var a = this.serializeArray();
    $.each(a, function() {
        if (o[this.name] !== undefined) {
            if (!o[this.name].push) {
                o[this.name] = [o[this.name]];
            }
            o[this.name].push(this.value || '');
        } else {
            o[this.name] = this.value || '';
        }
    });
    return o;
};

var veil = veil || {};

veil.log = function(message) {
    if(typeof console === "undefined"){
    }else{
        console.log(message);
    }
};

executed = [];
veil.executeOnce = function (hash, func) {
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
    var onError = options.onError;
    var onValidationError = options.onValidationError;
    var dataType = options.dataType;
    var data = options.data;
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
                alert('用户名、密码错误或登录超时');
                window.location.href='/login';
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
                alert('用户名、密码错误或登录超时');
                window.location.href='/login';
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
                alert('用户名、密码错误或登录超时');
                window.location.href='/login';
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
                alert('用户名、密码错误或登录超时');
                window.location.href='/login';
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
    var _ = {
        type:'DELETE',
        url:url,
        success:onSuccess,
        statusCode:{
            401: function(){
                alert('用户名、密码错误或登录超时');
                window.location.href='/login';
            },
            403:function() {alert('权限不足');}
        }
    };
    return $.ajax(_);
};

veil.widget = {};

veil.widget.handle = function (widget_selector, child_selector, event, handler) {
    $(document).on(event, widget_selector + ' ' + child_selector, function () {
        var widget = $(this).parents(widget_selector);
        var newArgs = [widget];
        for(var i = 0; i < arguments.length; i++) {
            newArgs.push(arguments[i]);
        }
        return handler.apply(this, newArgs);
    });
};

veil.widget.delResource = function (widget, onSuccess) {
    var _ = {
        url:widget.data('deleteUrl'),
        onSuccess:function () {
            widget.remove();
            onSuccess();
        }
    };
    return veil.resource.del(_);
};

veil.widget.createResource = function (widget, onSuccess, data, dataFormat, dataType) {
    veil.widget.clearErrorMessages(widget);
    if (typeof(data) === 'undefined') {
        data = dataFormat === 'json' ? widget.serializeObject() : widget.serialize();
    }
    var _ = {
        url: widget.attr('action'),
        data: data,
        dataFormat: dataFormat,
        dataType: dataType,
        onSuccess: function (s) {
            widget[0].reset();
            onSuccess(s);
        },
        onError: function () {
            //veil.widget.showErrorMessage(widget, '操作失败');
        },
        onValidationError: function (xhr) {
            if (xhr.getResponseHeader('Content-Type').indexOf('application/json') != -1) {
                widget.data('errors', $.parseJSON(xhr.responseText));
                veil.widget.showFieldErrorMessage(widget);
            } else {
                veil.widget.processWidget(xhr.responseText, function(html){
                    var newWidget = $(html);
                    widget.replaceWith(newWidget);
                    widget = newWidget;
                    veil.widget.showErrorMessage(widget, '提交的信息未被服务器接受');
                    veil.widget.showFieldErrorMessage(widget);
                });
            }
        }
    };
    return veil.resource.create(_);
};

veil.widget.patchResource = function(widget, onSuccess, data, dataFormat, dataType) {
    veil.widget.clearErrorMessages(widget);
    if (typeof(data) === 'undefined') {
        data = dataFormat === 'json' ? widget.serializeObject() : widget.serialize();
    }
    var _ = {
        url: widget.attr('action'),
        data: data || widget.serialize(),
        dataFormat: dataFormat,
        dataType: dataType,
        onSuccess: function (s) {
            widget[0].reset();
            onSuccess(s);
        },
        onError: function () {
            //veil.widget.showErrorMessage(widget, '操作失败');
        },
        onValidationError: function (xhr) {
            if (xhr.getResponseHeader('Content-Type').indexOf('application/json') != -1) {
                widget.data('errors', $.parseJSON(xhr.responseText));
                veil.widget.showFieldErrorMessage(widget);
            } else {
                veil.widget.processWidget(xhr.responseText, function(html){
                    var newWidget = $(html);
                    widget.replaceWith(newWidget);
                    widget = newWidget;
                    veil.widget.showErrorMessage(widget, '提交的信息未被服务器接受');
                    veil.widget.showFieldErrorMessage(widget);
                });
            }
        }
    };
    return veil.resource.patch(_);
};

veil.widget.updateResource = function (widget, onSuccess, data, dataFormat, dataType) {
    veil.widget.clearErrorMessages(widget);
    if (typeof(data) === 'undefined') {
        data = dataFormat === 'json' ? widget.serializeObject() : widget.serialize();
    }
    var _ = {
        url:widget.attr('action'),
        data: data || widget.serialize(),
        dataFormat: dataFormat,
        dataType: dataType,
        onSuccess: function (s) {
            widget[0].reset();
            onSuccess(s);
        },
        onError: function () {
            //veil.widget.showErrorMessage(widget, '操作失败');
        },
        onValidationError: function (xhr) {
            if (xhr.getResponseHeader('Content-Type').indexOf('application/json') != -1) {
                widget.data('errors', $.parseJSON(xhr.responseText));
                veil.widget.showFieldErrorMessage(widget);
            } else {
                veil.widget.processWidget(xhr.responseText, function(html){
                    var newWidget = $(html);
                    widget.replaceWith(newWidget);
                    widget = newWidget;
                    veil.widget.showErrorMessage(widget, '提交的信息未被服务器接受');
                    veil.widget.showFieldErrorMessage(widget);
                });
            }
        }
    };
    return veil.resource.update(_);
};

veil.widget.getResource = function (widget, onSuccess) {
    veil.widget.clearErrorMessages(widget);
    var _ = {
        url:widget.attr('action'),
        data:widget.serialize(),
        onSuccess:function (html) {
            widget[0].reset();
            veil.widget.processWidget(html, onSuccess);
        },
        onError:function () {
            //veil.widget.showErrorMessage(widget, '操作失败');
        },
        onValidationError:function (xhr) {
            if (xhr.getResponseHeader('Content-Type').indexOf('application/json') != -1) {
                widget.data('errors', $.parseJSON(xhr.responseText));
                veil.widget.showFieldErrorMessage(widget);
            } else {
                veil.widget.processWidget(xhr.responseText, function(html){
                    var newWidget = $(html);
                    widget.replaceWith(newWidget);
                    widget = newWidget;
                    veil.widget.showErrorMessage(widget, '提交的信息未被服务器接受');
                    veil.widget.showFieldErrorMessage(widget);
                });
            }
        }
    };
    return veil.resource.get(_);
};

veil.widget.showErrorMessage = function (widget, defaultErrorMessage) {
    var errorMessage = widget.data('error-message') || defaultErrorMessage;
    widget.prepend(
        '<span class="error-message label label-warning summary-error-message">' +
            '<i class="icon-info-sign"></i>' +
            errorMessage + '</span>');
};

veil.widget.showFieldErrorMessage = function (widget) {
    var allErrors = widget.data('errors');
    for (var field in allErrors) {
        if (allErrors.hasOwnProperty(field)) {
            var errors = $(allErrors[field]);
            if(typeof allErrors[field] == 'string') {
                errors = $([allErrors[field]]);
            }
            errors.each(function () {
                var error = this;
                var $field = widget.find('[name=' + field + ']');
                var $error = $('<span class="error-message label label-warning"><i class="icon-info-sign"></i>'
                    + error + '</span>');
                $error.insertAfter( $field );
            });
        }
    }
};

veil.widget.clearErrorMessages = function (widget) {
    widget.find('.error-message').remove();
};

veil.widget.refresh = function (widget, options) {
    options = options || {};
    var refreshUrl = options.refreshUrl || widget.data('refreshUrl');
    var data=options.data;
    var onSuccess = options.onSuccess;
    if (refreshUrl) {
        veil.resource.get({
            url:refreshUrl,
            data:data,
            onSuccess:function (html) {
                veil.widget.processWidget(html, function(html) {
                    var token = 'refreshed-' + Math.round(Math.random()*1000);
                    widget.replaceWith($(html).attr('data-refresh-token', token));
                    var refreshedWidget = $('[data-refresh-token=' + token + ']');
                    if (!refreshedWidget.length) {
                        veil.log('widget disappeared after refreshed from: ' + refreshUrl);
                    } else {
                        if (onSuccess) {
                            onSuccess(refreshedWidget)
                        }
                    }
                });
            }
        });
    }else{
        veil.log('missing refreshUrl');
    }
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

veil.widget.loadedJavascripts = [];
veil.widget.loadedStylesheets = [];
veil.widget.RE_SCRIPT = /<script.*?><\/script>/ig;
veil.widget.RE_LINK = /<link.*?\/?>(<\/link>)?/ig;
veil.widget.initializers = [];
veil.widget.processWidget = function (html, processHtml) {
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
                var link;
                if(document.createStyleSheet) {
                    link = document.createStyleSheet(url);
                }
                else {
                    link = document.createElement('link');
                    link.rel = 'stylesheet';
                    link.type = 'text/css';
                    link.href = url;
                }
                $('body').append(link);
            }
        }
    }
    var javascriptUrls = [];
    html = html.replace(veil.widget.RE_SCRIPT, function (scriptElement) {
        javascriptUrls.push($(scriptElement).attr('src'));
        return '';
    });
    html = html.replace(veil.widget.RE_LINK, function (linkElement) {
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
    processHtml(html);
    $(javascriptUrls).each(function() {
        loadJavascript(this);
    });
    $(veil.widget.initializers).each(function() {
        this();
    });
};
