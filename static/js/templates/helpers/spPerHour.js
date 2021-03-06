define('templates/helpers/spPerHour', ['hbs/handlebars'], 
    function(Handlebars) {
        
        function spPerHour(skill) {
            var attr = {164: skill.charisma, 
				165: skill.intelligence,
				166: skill.memory,
				167: skill.perception,
				168: skill.willpower
			};
			return (attr[skill.primary_attribute] + attr[skill.secondary_attribute]/2) * 60;
        }

        Handlebars.registerHelper('spPerHour', spPerHour);
        return spPerHour;
    }
);