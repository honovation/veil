function executeAndStripScripts(html) {
    while (true) {
        var scriptTag = /<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>/gi.exec(html);
        if (scriptTag) {
            html = html.replace(scriptTag, '');
            var tempDoc = $($.parseXML('<xml>' + scriptTag + '</xml>'));
            var url = tempDoc.find('script').attr('src');
            var script = document.createElement('script');
            script.type = 'text/javascript';
            script.src = url;
            $('body').append(script);
        } else {
            break;
        }
    }
    return html;
}