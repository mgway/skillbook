define('templates/helpers/splitString', ['hbs/handlebars'], 
    function(Handlebars) {
        function splitString(context, options) {
            var sep = options.hash.delim !== undefined? options.hash.delim : ":";
            var str = context.split(sep);
            var position = options.hash.position !== undefined? options.hash.position : 0;
            return str[position];
        }
        
        Handlebars.registerHelper('splitString', splitString);
        return splitString;
    }
);