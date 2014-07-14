define('templates/helpers/decodeAttribute', ['hbs/handlebars'], 
    function(Handlebars) {
        function decodeAttribute(attribute, options) {
            var attributes = {164:'Charisma', 165:'Intelligence', 
                    166:'Memory', 167:'Perception', 168:'Willpower'};
            return attributes[attribute];
        }
        
        Handlebars.registerHelper('decodeAttribute', decodeAttribute);
        return decodeAttribute;
    }
);