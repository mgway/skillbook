define('templates/helpers/spPerHour', ['hbs/handlebars'], 
    function(Handlebars) {
        
        function spPerHour(character, primary_attribute, secondary_attribute) {
            var attr = {164: character.charisma, 
				165: character.intelligence,
				166: character.memory,
				167: character.perception,
				168: character.willpower
			};
			return (attr[primary_attribute] + attr[secondary_attribute]/2) * 60;
        }

        Handlebars.registerHelper('spPerHour', spPerHour);
        return spPerHour;
    }
);