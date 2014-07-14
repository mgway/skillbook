define('templates/helpers/spNextLevel', ['hbs/handlebars'], 
    function(Handlebars) {
        function spNextLevel(level, multiplier, options) {
            var levels = [250, 1415, 8000, 45255, 256000];
            return commas(levels[Math.min(level, 4)] * multiplier);
        }
        
        // Since handlebars doesn't support nested helpers, some duplication
        function commas(number, options) {
            var i = parseInt(Math.abs(number)) + '';
            var j = ((j = i.length) > 3) ? j % 3 : 0;
            return (j ? i.substr(0, j) + ',' : '') + i.substr(j).replace(/(\d{3})(?=\d)/g, "$1" + ',');
        }
        
        Handlebars.registerHelper('spNextLevel', spNextLevel);
        return spNextLevel;
    }
);