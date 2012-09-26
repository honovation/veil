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

veil.resource.get = function (url, onSuccess) {
    $.get(url, function (html) {
        onSuccess(veil.widget.processWidget(html));
    });
};

veil.resource.create = function (options) {
    var url = options.url;
    var data = options.data;
    var onSuccess = options.onSuccess;
    var onError = options.onError;
    var onValidationError = options.onValidationError;
    var _ = {
        type:'POST',
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

veil.widget.createResource = function (widget, onSuccess) {
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
    var allErrorMessage = widget.data('errors');
    for (var field in allErrorMessage) {
        widget.prepend('<span class="error-message label label-warning">' +
        '<i class="icon-info-sign"></i>' + allErrorMessage[field] + '</span>');
    }
};

veil.widget.clearErrorMessages = function(widget) {
    widget.find('.error-message').remove();
};

veil.widget.refresh = function (widget) {
    veil.resource.get(widget.data('refresh-url'), function (html) {
        widget.replaceWith(html);
    });
};

veil.widget.loadedJavascripts = [];
veil.widget.loadedStylesheets = [];
veil.widget.toXML = function (xmlDocument) {
    if (window.ActiveXObject) {
        return xmlDocument.xml;
    } else {
        return (new XMLSerializer()).serializeToString(xmlDocument);
    }
};
var RE_SCRIPT = /<script.*?><\/script>/ig;
var RE_SRC_ATTRIBUTE = /.*?src="(.*?)"/i;
veil.widget._processWidget = function(html) {
    var js_urls = [];
    html = html.replace(RE_SCRIPT, function(script_element) {
        console.log('!!! ' + script_element.replace(RE_SRC_ATTRIBUTE, '$1'));
        return '';
    });
    return html;
};
veil.widget.processWidget = function (html) {
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

    var doc = $.parseXML('<dummy-wrapper>' + html + '</dummy-wrapper>');

    $(doc).find('script').each(function () {
        var $script = $(this);
        if ('text/plain' == $script.attr('type')) {
            return
        }
        if ($script.attr('src')) {
            loadJavascript($script.attr('src'));
        } else {
            veil.log('can only load javascript from url');
        }
        $script.remove();
    });
    $(doc).find('style').each(function () {
        var $style = $(this);
        veil.log('can only load stylesheet from url');
        $style.remove();
    });
    $(doc).find('link').each(function () {
        var $link = $(this);
        if ('stylesheet' == $link.attr('rel')) {
            loadStylesheet($link.attr('href'));
            $link.remove();
        }
    });
    $(doc).find('[data-errors]').each(function () {
        var $form = $(this);
        var all_errors = $form.data('errors');
        for (var field in all_errors) {
            if (all_errors.hasOwnProperty(field)) {
                var errors = $(all_errors[field]);
                errors.each(function () {
                    var error = this;
                    $('<span class="error-message label label-warning"><i class="icon-info-sign"></i>'
                          + error + '</span>').insertBefore(
                        $form.find('[name=' + field + ']')
                    );
                });
            }
        }
    });
    return veil.widget.toXML(doc).replace('<dummy-wrapper>', '').replace('</dummy-wrapper>', '').replace('<dummy-wrapper/>', '');
};
