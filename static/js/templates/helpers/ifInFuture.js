define('templates/helpers/ifInFuture', ['hbs/handlebars', 'moment'], 
    function(Handlebars, moment) {
        function ifInFuture(time, options) {
            if (time !== undefined && moment.utc(time) >= moment()) {
                return options.fn(this);
            } else {
                return options.inverse(this);
            }
        }
        
        Handlebars.registerHelper('ifInFuture', ifInFuture);
        return ifInFuture;
    }
);