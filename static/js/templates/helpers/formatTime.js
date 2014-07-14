define('templates/helpers/formatTime', ['hbs/handlebars', 'moment'], 
    function(Handlebars, moment) {
        function formatTime(context, options) {
            if (context !== undefined) {
                if (context._isAMomentObject === undefined)
                    return moment.utc(context).local().format('llll');
                else
                    return context.format('llll');
            } else {
                return "";
            }
        }
        
        Handlebars.registerHelper('formatTime', formatTime);
        return formatTime;
    }
);