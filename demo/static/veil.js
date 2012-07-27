var veil = veil || {};

veil.event = {};

veil.event.handle = function (eventName, handler) {
    $(document).bind(eventName, handler);
};

veil.event.trigger = function (eventName, args) {
    $(document).trigger(eventName, args);

    if (veil.event.hasDelegation(eventName)) {
        $(veil.event.DELEGATIONS[eventName]).each(function () {
            veil.event.trigger(this, args);
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
    $.get(url, function (html) {
        onSuccess(veil.resource.stripScripts(html));
    });
};

veil.resource.refreshWidget = function (widget) {
    var _ = {
        url: widget.data('refresh-url'),
        onSuccess: function (html) {
            widget.replaceWith(html);
        }
    };
    veil.resource.get(_);
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

veil.resource.createFromWidget = function (widget, onSuccess) {
    widget.find('.error-messages').html('');
    widget.find('.having-error').removeClass('having-error');
    var _ = {
        url:'/resources/items',
        data:widget.serialize(),
        onSuccess:function () {
            widget[0].reset();
            onSuccess();
        },
        onError:function () {
            veil.showMessage(widget.data('error-message'));
        },
        onValidationError:function (xhr) {
            widget.replaceWith(veil.resource.stripScripts(xhr.responseText));
        }
    };
    veil.resource.create(_);
};

veil.resource.delete = function(options) {
    var url = options.url;
    var onSuccess = options.onSuccess;
    var _ = {
        type: 'DELETE',
        url: url,
        success: onSuccess
    };
    $.ajax(_);
};

veil.resource.deleteFromWidget = function(widget) {
    var _ = {
        url: widget.data('delete-url'),
        onSuccess: function() {
            widget.remove();
        }
    };
    veil.resource.delete(_);
};

veil.resource.stripScripts = function (html, executes) {
    while (true) {
        var scriptTag = /<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>/gi.exec(html);
        if (scriptTag) {
            html = html.replace(scriptTag, '');
            if (executes) {
                var tempDoc = $($.parseXML('<xml>' + scriptTag + '</xml>'));
                var url = tempDoc.find('script').attr('src');
                var script = document.createElement('script');
                script.type = 'text/javascript';
                script.src = url;
                $('body').append(script);
            }
        } else {
            break;
        }
    }
    return html;
};