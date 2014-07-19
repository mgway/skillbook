define(
    [
        'jquery', 
        'common/preciseMoment'
    ],
    function ($, moment) {
 
       return function() {
            $('span[data-expiration]').each(function(idx, el) {
                el = $(el);
                var expiration = moment.utc(el.data('expiration'));
                var now = moment.utc();
                
                el.text(now.preciseDiff(expiration));
                
                if (expiration - now < 86400000) {
                    el.addClass('error');
                } else {
                    el.removeClass('error');
                }
            });
        };
    }
);