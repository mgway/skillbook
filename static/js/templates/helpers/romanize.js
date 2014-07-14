define('templates/helpers/romanize', ['hbs/handlebars'], 
    function(Handlebars) {
        function romanize(context, options) {
            if (context !== undefined)
                // The elusive roman numeral zero
                return [0, 'I', 'II', 'III', 'IV', 'V'][context];
            else
                return "";
        }
        
        Handlebars.registerHelper('romanize', romanize);
        return romanize;
    }
);