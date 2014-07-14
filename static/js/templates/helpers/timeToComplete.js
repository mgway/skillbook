define('templates/helpers/timeToComplete', ['hbs/handlebars'], 
    function(Handlebars) {
        
        function timeToComplete(skill) {
            var attr = {164: skill.charisma, 
				165: skill.intelligence,
				166: skill.memory,
				167: skill.perception,
				168: skill.willpower
			};
			
			var sp_hour = spPerHour(attr[skill.primaryattr], attr[skill.secondaryattr]);
			var sp_required = spNextLevel(skill.level, skill.timeconstant) - skill.skillpoints;
			//var response = {'seconds': (sp_required/sp_hour) * 3600, 'sp_hour': sp_hour, 'sp_required': sp_required};
			return formatSeconds((sp_required/sp_hour) * 3600);
        }
        
        function spPerHour(primary, secondary) {
			return (primary + secondary/2) * 60;
        }
        
        function spNextLevel(level, multiplier, options) {
            var levels = [250, 1415, 8000, 45255, 256000];
            return levels[Math.min(level, 4)] * multiplier;
        }
        
        function formatSeconds(sec) {
			if(sec === 0) {
				return "None";
			}
			var days = parseInt(sec / 86400) % 30;
			var hours = parseInt(sec / 3600) % 24;
			var minutes = parseInt(sec / 60) % 60;
			var seconds = parseInt(sec) % 60;
			var day_s = days == 1? " day, " : " days, ";
			var hour_s = hours == 1? " hour, " : " hours, ";
			var minute_s = minutes == 1? " minute, " : " minutes, ";
			var second_s = seconds == 1? " second" : " seconds";
			return ((days > 0)? days+day_s:"") + ((hours > 0)?hours + hour_s: "") + minutes + minute_s + seconds + second_s;
		}

        
        Handlebars.registerHelper('timeToComplete', timeToComplete);
        return timeToComplete;
    }
);