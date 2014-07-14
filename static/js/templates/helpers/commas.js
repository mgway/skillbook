define('templates/helpers/commas', ['hbs/handlebars'], 
    function(Handlebars) {
        function commas(context, options) {
            var i = parseInt(Math.abs(context)) + '';
            var j = ((j = i.length) > 3) ? j % 3 : 0;
            return (j ? i.substr(0, j) + ',' : '') + i.substr(j).replace(/(\d{3})(?=\d)/g, "$1" + ',');
        }
        
        Handlebars.registerHelper('commas', commas);
        return commas;
    }
);