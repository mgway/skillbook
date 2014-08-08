define(function(require) {
    'use strict';
    var $ = require('jquery');
 
    return function() {
        function getCookie(name) {
            var r = document.cookie.match("\\b" + name + "=([^;]*)\\b");
            return r ? r[1] : undefined;
        }
            
        this.get = function(options) {
            this.ajax(options, 'get');
        };
 
        this.post = function(options) {
            this.ajax(options, 'post');
        };
 
        this.ajax = function(options, type) {
            var xhr = $.extend(options.xhr, {
                context: this,
                type: type,
                dataType: 'json',
                headers: {'X-Xsrftoken': getCookie('_xsrf')}
            });
            var events  = options.events;
            var meta = (typeof options.meta === 'object' ? options.meta : {});
 
            if (typeof events.before === 'string') {
                this.trigger(events.before);
                delete events.before;
            }
 
            var req = $.ajax(xhr);
            $.each(events, function(key, value) {
                if (typeof value === 'string') {
                    req[key](function() {
                        var ret = {meta: meta};
                        ret[meta.key] = req.responseJSON;
                        this.trigger(value, ret);
                    });
                }
            });
        };
    };
});